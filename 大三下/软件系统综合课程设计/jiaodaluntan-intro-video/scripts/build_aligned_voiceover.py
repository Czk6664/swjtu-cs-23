"""Build a subtitle-aligned Chinese voiceover for the rendered video.

The script reads the current subtitle clips from index.html, generates one TTS
file per subtitle with edge-tts, and muxes the natural-speed narration into the
rendered MP4 at the subtitle start times.
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import re
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

import edge_tts


DEFAULT_VOICE = "zh-CN-YunyangNeural"
DEFAULT_RATE = "+0%"
DEFAULT_VOLUME = "+0%"
DEFAULT_PITCH = "+0Hz"


@dataclass
class Caption:
    index: int
    clip_id: str
    start: float
    duration: float
    text: str

    @property
    def end(self) -> float:
        return self.start + self.duration


class SubtitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.captions: list[Caption] = []
        self._current: dict[str, object] | None = None
        self._in_sub_text = False
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k: v or "" for k, v in attrs}
        classes = attr.get("class", "").split()
        if tag == "div" and "sub-clip" in classes:
            self._current = {
                "clip_id": attr.get("id", f"sub{len(self.captions) + 1}"),
                "start": float(attr["data-start"]),
                "duration": float(attr["data-duration"]),
            }
            self._text_parts = []
        elif self._current is not None and tag == "span" and "sub-text" in classes:
            self._in_sub_text = True

    def handle_data(self, data: str) -> None:
        if self._in_sub_text:
            self._text_parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._in_sub_text:
            self._text_parts.append(html.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        if self._in_sub_text:
            self._text_parts.append(html.unescape(f"&#{name};"))

    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self._in_sub_text:
            self._in_sub_text = False
        elif tag == "div" and self._current is not None:
            text = re.sub(r"\s+", " ", "".join(self._text_parts)).strip()
            if text:
                self.captions.append(
                    Caption(
                        index=len(self.captions) + 1,
                        clip_id=str(self._current["clip_id"]),
                        start=float(self._current["start"]),
                        duration=float(self._current["duration"]),
                        text=text,
                    )
                )
            self._current = None
            self._text_parts = []


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, encoding="utf-8", errors="replace")


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def read_captions(index_path: Path) -> list[Caption]:
    parser = SubtitleParser()
    parser.feed(index_path.read_text(encoding="utf-8"))
    parser.close()
    if not parser.captions:
        raise RuntimeError(f"No subtitle clips found in {index_path}")
    return parser.captions


async def generate_segment(caption: Caption, out_path: Path, voice: str, rate: str, volume: str, pitch: str) -> None:
    communicate = edge_tts.Communicate(
        text=caption.text,
        voice=voice,
        rate=rate,
        volume=volume,
        pitch=pitch,
    )
    await communicate.save(str(out_path))


async def generate_all(captions: list[Caption], raw_dir: Path, voice: str, rate: str, volume: str, pitch: str) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for caption in captions:
        out_path = raw_dir / f"{caption.index:02d}_{caption.clip_id}.mp3"
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"[tts] keep {out_path.name}")
            continue
        print(f"[tts] {caption.index:02d} {caption.start:.3f}-{caption.end:.3f}s {caption.text}")
        await generate_segment(caption, out_path, voice, rate, volume, pitch)


def measure_all(captions: list[Caption], raw_dir: Path, video_duration: float) -> list[dict[str, object]]:
    manifest: list[dict[str, object]] = []
    for caption in captions:
        raw_path = raw_dir / f"{caption.index:02d}_{caption.clip_id}.mp3"
        raw_duration = probe_duration(raw_path)
        actual_end = caption.start + raw_duration
        duration_error = raw_duration - caption.duration
        print(
            f"[measure] {caption.index:02d} raw={raw_duration:.3f}s "
            f"caption={caption.duration:.3f}s end={actual_end:.3f}s"
        )
        if actual_end - video_duration > 0.05:
            raise RuntimeError(
                f"Clip {caption.index:02d} ends at {actual_end:.3f}s, beyond video {video_duration:.3f}s"
            )
        manifest.append(
            {
                "index": caption.index,
                "clip_id": caption.clip_id,
                "text": caption.text,
                "start": caption.start,
                "duration": caption.duration,
                "end": caption.end,
                "raw_file": str(raw_path),
                "raw_duration": raw_duration,
                "actual_end": actual_end,
                "duration_error": duration_error,
            }
        )
    return manifest


def mux_voiceover(video_path: Path, output_path: Path, captions: list[Caption], raw_dir: Path) -> None:
    video_duration = probe_duration(video_path)
    inputs: list[str] = []
    delays: list[str] = []
    mix_labels: list[str] = []
    for zero_based, caption in enumerate(captions):
        raw_path = raw_dir / f"{caption.index:02d}_{caption.clip_id}.mp3"
        inputs.extend(["-i", str(raw_path)])
        delay_ms = int(round(caption.start * 1000))
        label = f"a{zero_based}"
        delays.append(f"[{zero_based + 1}:a]adelay={delay_ms}:all=1[{label}]")
        mix_labels.append(f"[{label}]")

    filter_complex = (
        ";".join(delays)
        + ";"
        + "".join(mix_labels)
        + f"amix=inputs={len(captions)}:duration=longest:normalize=0,"
        + f"atrim=0:{video_duration:.6f},asetpts=N/SR/TB[aout]"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "warning",
            "-i",
            str(video_path),
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-t",
            f"{video_duration:.6f}",
            str(output_path),
        ]
    )


def write_manifest(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    if "\ufffd" in text:
        raise RuntimeError(f"Encoding verification failed for {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="index.html")
    parser.add_argument("--video", default="renders/jiaodaluntan-intro-video-beautified.mp4")
    parser.add_argument("--output", default="renders/jiaodaluntan-intro-video-beautified-voiceover-natural.mp4")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--rate", default=DEFAULT_RATE)
    parser.add_argument("--volume", default=DEFAULT_VOLUME)
    parser.add_argument("--pitch", default=DEFAULT_PITCH)
    parser.add_argument("--work-dir", default="assets/voiceover_aligned")
    args = parser.parse_args()

    index_path = Path(args.index)
    video_path = Path(args.video)
    output_path = Path(args.output)
    work_dir = Path(args.work_dir)
    raw_dir = work_dir / "raw"
    manifest_path = work_dir / "manifest.json"

    captions = read_captions(index_path)
    total = probe_duration(video_path)
    last_caption_end = max(c.end for c in captions)
    if last_caption_end - total > 0.05:
        raise RuntimeError(
            f"Last caption ends at {last_caption_end:.3f}s, beyond video duration {total:.3f}s"
        )

    print(f"[captions] {len(captions)} clips, video {total:.3f}s")
    asyncio.run(generate_all(captions, raw_dir, args.voice, args.rate, args.volume, args.pitch))
    manifest = measure_all(captions, raw_dir, total)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mux_voiceover(video_path, output_path, captions, raw_dir)

    final_duration = probe_duration(output_path)
    max_duration_error = max(abs(float(item["duration_error"])) for item in manifest)
    write_manifest(
        manifest_path,
        {
            "voice": args.voice,
            "rate": args.rate,
            "volume": args.volume,
            "pitch": args.pitch,
            "video": str(video_path),
            "output": str(output_path),
            "video_duration": total,
            "final_duration": final_duration,
            "max_duration_error": max_duration_error,
            "clips": manifest,
        },
    )

    if max_duration_error > 0.08:
        raise RuntimeError(
            f"Subtitle durations do not match natural voice length; max error {max_duration_error:.3f}s"
        )
    if abs(final_duration - total) > 0.08:
        raise RuntimeError(f"Output duration {final_duration:.3f}s differs from video {total:.3f}s")

    print(f"[done] {output_path}")
    print(f"[manifest] {manifest_path}")
    print(f"[verify] max duration error {max_duration_error:.4f}s, final {final_duration:.3f}s")


if __name__ == "__main__":
    main()
