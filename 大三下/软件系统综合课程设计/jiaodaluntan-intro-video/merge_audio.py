"""Merge individual voiceover MP3s into a single audio track and combine with video."""
import subprocess
import sys
import os

TIMINGS_MS = [800, 3800, 7800, 11800, 15800, 19800, 23800, 27800, 31800, 35800, 39800, 43800, 47800, 51800, 55800]
VOICEOVER_DIR = "assets/voiceover"
TOTAL_DURATION = 60

def main():
    if len(sys.argv) < 2:
        print("Usage: python merge_audio.py <rendered_video.mp4> [output.mp4]")
        sys.exit(1)

    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "final_with_voiceover.mp4"

    inputs = []
    adelay_parts = []
    valid = 0

    for i in range(1, 16):
        mp3 = os.path.join(VOICEOVER_DIR, f"s{i:02d}.mp3")
        if not os.path.exists(mp3):
            print(f"Warning: {mp3} not found, skipping")
            continue
        inputs.extend(["-i", mp3])
        delay = TIMINGS_MS[i - 1]
        adelay_parts.append(f"[{valid + 1}:a]adelay={delay}|{delay}[a{valid}]")
        valid += 1

    if valid == 0:
        print("No audio files found in assets/voiceover/")
        sys.exit(1)

    mix_inputs = "".join(f"[a{j}]" for j in range(valid))
    filter_complex = ";".join(adelay_parts) + f";{mix_inputs}amix=inputs={valid}:duration=longest[aout]"

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path,
    ]

    print("Running ffmpeg...")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"\nDone! Output: {output_path}")


if __name__ == "__main__":
    main()
