import asyncio
import websockets
import json
import ssl
import os

MODEL = "speech-2.8-hd"
VOICE_ID = "Chinese_radio_reporter_vv1"
FILE_FORMAT = "mp3"
OUTPUT_DIR = "assets/voiceover"

SCENES = [
    ("s01", "交大论坛，一站式校园社区平台。"),
    ("s02", "小红书式瀑布流首页，浏览最新帖子和热门推荐。"),
    ("s03", "安全注册，快速登录，无缝融入校园社区。"),
    ("s04", "富文本编辑器，支持图文发布与草稿自动保存。"),
    ("s05", "点赞、收藏、评论、举报，丰富的社区互动体验。"),
    ("s06", "版块导航与标签体系，快速发现感兴趣的内容。"),
    ("s07", "每日签到获取积分，等级体系激励用户活跃。"),
    ("s08", "积分商城，丰富的实物与虚拟奖品等你来兑换。"),
    ("s09", "关注好友，接收通知，打造你的社交网络。"),
    ("s10", "管理员仪表盘，实时掌握平台运营数据。"),
    ("s11", "内容审核、举报处理、推荐调控，全链路治理。"),
    ("s12", "Vite前端加Spring Boot后端，三层架构设计。"),
    ("s13", "完整覆盖软件工程核心知识的全流程实践。"),
    ("s14", "项目团队来自西南交通大学，软件系统综合课程设计。"),
    ("s15", "交大论坛，感谢观看。"),
]

# Subtitle start times (seconds) for ffmpeg merge
TIMINGS = [0.8, 3.8, 7.8, 11.8, 15.8, 19.8, 23.8, 27.8, 31.8, 35.8, 39.8, 43.8, 47.8, 51.8, 55.8]


async def generate_one(api_key, name, text):
    url = "wss://api.minimaxi.com/ws/v1/t2a_v2"
    headers = {"Authorization": f"Bearer {api_key}"}

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    ws = await websockets.connect(url, additional_headers=headers, ssl=ssl_context)
    connected = json.loads(await ws.recv())
    if connected.get("event") != "connected_success":
        print(f"  [{name}] Connection failed")
        await ws.close()
        return False

    start_msg = {
        "event": "task_start",
        "model": MODEL,
        "voice_setting": {
            "voice_id": VOICE_ID,
            "speed": 1,
            "vol": 1,
            "pitch": 0,
            "english_normalization": False,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": FILE_FORMAT,
            "channel": 1,
        },
    }
    await ws.send(json.dumps(start_msg))
    resp = json.loads(await ws.recv())
    if resp.get("event") != "task_started":
        print(f"  [{name}] Task start failed")
        await ws.close()
        return False

    await ws.send(json.dumps({"event": "task_continue", "text": text}))

    audio_data = b""
    while True:
        resp = json.loads(await ws.recv())
        if "data" in resp and "audio" in resp["data"]:
            audio = resp["data"]["audio"]
            if audio:
                audio_data += bytes.fromhex(audio)
        if resp.get("is_final"):
            break

    out_path = os.path.join(OUTPUT_DIR, f"{name}.{FILE_FORMAT}")
    with open(out_path, "wb") as f:
        f.write(audio_data)

    try:
        await ws.send(json.dumps({"event": "task_finish"}))
        await ws.close()
    except Exception:
        pass

    return True


async def main():
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("Error: set MINIMAX_API_KEY environment variable first")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i, (name, text) in enumerate(SCENES, 1):
        out_path = os.path.join(OUTPUT_DIR, f"{name}.{FILE_FORMAT}")
        if os.path.exists(out_path):
            print(f"[{i}/15] {name} already exists, skipping")
            continue
        print(f"[{i}/15] Generating {name}: {text}")
        ok = await generate_one(api_key, name, text)
        if ok:
            print(f"  -> Saved {out_path}")
        else:
            print(f"  -> FAILED {name}")

    print("\nAll done! Audio files are in assets/voiceover/")
    print("\nTo merge with rendered video, run:")
    print('  python merge_audio.py rendered_video.mp4')


if __name__ == "__main__":
    asyncio.run(main())
