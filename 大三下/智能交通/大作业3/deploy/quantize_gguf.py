r"""合并后的 HF 模型 -> GGUF F16 -> Q4_K_M 量化.

策略:
    1. pip install gguf  (装 llama.cpp 官方 Python 绑定)
    2. python -m gguf.scripts.convert_hf_to_gguf   把 HF -> F16 GGUF
    3. 用 llama-quantize.exe 把 F16 GGUF -> Q4_K_M GGUF

默认要求 --local-quantize 提供本地的 llama-quantize.exe (国内网络拉 GitHub/ HF 经常超时).
如果提供 --auto-download, 脚本会尝试从多个 GitHub 镜像拉 Windows prebuilt zip.

约定的目录结构 (相对路径默认基于此):
    workspace/
    ├── deploy/                  <- 本脚本所在目录
    ├── models/
    │   ├── DeepSeek-R1-Distill-Qwen-7B-merged/    (merge_lora.py 输出)
    │   ├── travelqa-q4km_work/                    (F16 GGUF 缓存, 可删)
    │   └── travelqa-q4km.gguf                     (最终 Q4_K_M, 4.7 GB)

用法 (最简, 默认相对路径, 需本地已有 quantize binary):
    cd deploy
    python quantize_gguf.py --local-quantize "D:\\tools\\llama-quantize.exe"

显式覆盖:
    python quantize_gguf.py --merged E:\\merged --out E:\\out.gguf --quant Q5_K_M
                              --local-quantize D:\\tools\\llama-quantize.exe

自动下载 (如果网络通):
    python quantize_gguf.py --auto-download
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


SCRIPT_DIR   = Path(__file__).resolve().parent
WORKSPACE    = SCRIPT_DIR.parent
DEFAULT_MERGED   = WORKSPACE / "models" / "DeepSeek-R1-Distill-Qwen-7B-merged"
DEFAULT_OUT      = WORKSPACE / "models" / "travelqa-q4km.gguf"
DEFAULT_WORK_DIR = WORKSPACE / "models" / "travelqa-q4km_work"


def ensure_pip_package(pkg: str, import_name: str | None = None) -> None:
    import_name = import_name or pkg
    try:
        __import__(import_name)
        print(f"[setup] {pkg} 已装")
    except ImportError:
        print(f"[setup] pip install {pkg}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", pkg])


def ensure_gguf() -> None:
    ensure_pip_package("gguf")


def github_release_assets() -> list[dict]:
    """走 GitHub API 拿 release assets 列表, 失败时返回 []"""
    bases = [
        "https://api.github.com/repos/ggerganov/llama.cpp/releases/latest",
        "https://gh-proxy.com/https://api.github.com/repos/ggerganov/llama.cpp/releases/latest",
        "https://gh-proxy.net/https://api.github.com/repos/ggerganov/llama.cpp/releases/latest",
    ]
    for url in bases:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "quantize_gguf.py"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
            print(f"[setup] GitHub release: {data.get('tag_name')}  (via {url[:40]}...)")
            return data.get("assets", [])
        except Exception as e:
            print(f"[setup] 失败: {url[:60]}... -> {type(e).__name__}")
    return []


def download_zip(url: str, dst: Path) -> None:
    """走 codeload.github.com 镜像 + 直连两个通道下载"""
    bases = [url]
    if "github.com" in url and "releases/download" in url:
        bases.insert(0, url.replace("github.com", "codeload.github.com"))
        bases.append("https://gh-proxy.com/" + url)
        bases.append("https://gh-proxy.net/" + url)
        bases.append("https://mirror.ghproxy.com/" + url)

    for try_url in bases:
        try:
            print(f"[setup] 下载: {try_url[:80]}...")
            req = urllib.request.Request(try_url, headers={"User-Agent": "quantize_gguf.py"})
            with urllib.request.urlopen(req, timeout=120) as resp, open(dst, "wb") as out:
                total = int(resp.headers.get("Content-Length") or 0)
                downloaded = 0
                chunk = 4 * 1024 * 1024
                while True:
                    buf = resp.read(chunk)
                    if not buf:
                        break
                    out.write(buf)
                    downloaded += len(buf)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r  {downloaded/1e6:.0f}/{total/1e6:.0f} MB  ({pct:.1f}%)", end="", flush=True)
                print()
            if dst.stat().st_size > 10_000_000:  # < 10MB 视为失败
                return
            print(f"[setup] 下载文件太小, 重试下一个源")
            dst.unlink()
        except Exception as e:
            print(f"[setup] 失败: {type(e).__name__}: {str(e)[:100]}")
            if dst.exists():
                dst.unlink()
    raise RuntimeError(f"所有下载源都失败. 请手动下载 zip 后用 --local-quantize 兜底")


def auto_download_quantize(work: Path) -> Path:
    assets = github_release_assets()
    candidates = [a for a in assets if a["name"].startswith("llama-") and a["name"].endswith("-bin-win-cuda-x64.zip")]
    if not candidates:
        candidates = [a for a in assets if a["name"].startswith("llama-") and a["name"].endswith("-bin-win-x64.zip")]
    if not candidates:
        names = [a["name"] for a in assets if "win" in a["name"].lower()][:5]
        raise RuntimeError(f"找不到 Windows prebuilt zip. 可用: {names}")

    candidates.sort(key=lambda a: a["name"], reverse=True)
    chosen = candidates[0]
    print(f"[setup] 选定: {chosen['name']}  ({chosen['size']/1e6:.1f} MB)")

    zip_path = work / chosen["name"]
    download_zip(chosen["browser_download_url"], zip_path)
    print(f"[setup] 解压 {zip_path} ...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(work)
    matches = list(work.rglob("llama-quantize.exe"))
    if not matches:
        raise FileNotFoundError("llama-quantize.exe not found in prebuilt zip")
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0]


def find_existing_quantize(work: Path) -> Path | None:
    matches = list(work.rglob("llama-quantize.exe"))
    return matches[0] if matches else None


def convert_hf_to_f16(merged: Path, f16_gguf: Path) -> None:
    if f16_gguf.exists() and f16_gguf.stat().st_size > 1e9:
        print(f"[gguf] F16 已存在, 跳过: {f16_gguf}")
        return
    print(f"[gguf] Step 1: HF -> F16 GGUF")
    print(f"  merged : {merged}")
    print(f"  outfile: {f16_gguf}")
    f16_gguf.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-m", "gguf.scripts.convert_hf_to_gguf",
        str(merged),
        "--outfile", str(f16_gguf),
        "--outtype", "f16",
    ]
    print(f"  $ {' '.join(cmd)}")
    subprocess.check_call(cmd)


def quantize(qbin: Path, f16_gguf: Path, out_gguf: Path, quant: str) -> None:
    out_gguf.parent.mkdir(parents=True, exist_ok=True)
    print(f"[gguf] Step 2: F16 -> {quant}")
    print(f"  in : {f16_gguf} ({f16_gguf.stat().st_size/1e9:.2f} GB)")
    print(f"  out: {out_gguf}")
    cmd = [str(qbin), str(f16_gguf), str(out_gguf), quant]
    print(f"  $ {' '.join(cmd)}")
    subprocess.check_call(cmd)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--merged", default=str(DEFAULT_MERGED),
                   help=f"merge_lora.py 输出的 HF 目录 (默认 {DEFAULT_MERGED})")
    p.add_argument("--out", default=str(DEFAULT_OUT),
                   help=f"最终 GGUF 路径 (默认 {DEFAULT_OUT})")
    p.add_argument("--quant", default="Q4_K_M",
                   help="量化档位: Q2_K Q3_K_S Q3_K_M Q4_0 Q4_K_S Q4_K_M Q5_0 Q5_K_S Q5_K_M Q6_K Q8_0")
    p.add_argument("--work-dir", default=str(DEFAULT_WORK_DIR),
                   help=f"中间产物目录 (默认 {DEFAULT_WORK_DIR})")
    p.add_argument("--local-quantize", default=None,
                   help="已有 llama-quantize.exe 路径 (推荐, 国内网络拉 GitHub 经常超时)")
    p.add_argument("--auto-download", action="store_true",
                   help="自动从 GitHub 拉 Windows prebuilt zip (需能访问 GitHub 或其镜像)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    merged    = Path(args.merged).resolve()
    out_gguf  = Path(args.out).resolve()
    work      = Path(args.work_dir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    f16_gguf  = work / "f16.gguf"

    print(f"[gguf] 工作目录  : {SCRIPT_DIR}")
    print(f"[gguf] 合并后 HF : {merged}")
    print(f"[gguf] 最终 GGUF : {out_gguf}")
    print(f"[gguf] 量化档位  : {args.quant}")
    print(f"[gguf] 中间产物  : {work}")

    if not (merged / "config.json").exists():
        sys.exit(f"[gguf] 找不到 {merged}/config.json —— 请先跑 merge_lora.py")

    ensure_gguf()

    # 获取 quantize binary
    qbin = None
    if args.local_quantize:
        qbin = Path(args.local_quantize).resolve()
        if not qbin.exists():
            sys.exit(f"[setup] --local-quantize 指定的文件不存在: {qbin}")
        print(f"[setup] 使用本地 quantize: {qbin}")
    elif args.auto_download:
        qbin = find_existing_quantize(work) or auto_download_quantize(work)
    else:
        # 默认先看 work 目录有没有, 再提示用户
        qbin = find_existing_quantize(work)
        if not qbin:
            sys.exit(
                "\n[setup] 需要 llama-quantize.exe, 三个方式任选其一:\n"
                "  1. --local-quantize \"D:\\tools\\llama-quantize.exe\"  (推荐, 手动下载)\n"
                "  2. --auto-download  (脚本自动从 GitHub 拉, 需网络可达)\n"
                "  3. 把 llama-quantize.exe 放到 work 目录, 重跑脚本\n"
                "\n"
                "  手动下载 zip 步骤 (任一可访问 GitHub 的机器):\n"
                "  a) 浏览器打开 https://github.com/ggerganov/llama.cpp/releases/latest\n"
                "  b) 下载 llama-b*-bin-win-cuda-x64.zip (约 100-300 MB)\n"
                "  c) 解压得到 llama-quantize.exe\n"
                "  d) python quantize_gguf.py --local-quantize \"C:\\path\\to\\llama-quantize.exe\"\n"
            )

    print(f"[setup] quantize binary: {qbin}")
    convert_hf_to_f16(merged, f16_gguf)
    print(f"[gguf] F16 完成: {f16_gguf} ({f16_gguf.stat().st_size/1e9:.2f} GB)")

    if out_gguf.exists() and out_gguf.stat().st_size > 1e9:
        print(f"[gguf] 输出已存在, 跳过: {out_gguf} ({out_gguf.stat().st_size/1e9:.2f} GB)")
    else:
        quantize(qbin, f16_gguf, out_gguf, args.quant)

    print(f"[gguf] 完成. 最终模型: {out_gguf} ({out_gguf.stat().st_size/1e9:.2f} GB)")
    print(f"[gguf] 下一步: copy Modelfile 同目录, 然后 ollama create travelqa -f Modelfile")


if __name__ == "__main__":
    main()
