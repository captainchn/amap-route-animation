#!/usr/bin/env python3
"""Encode captured frames into an mp4 with ffmpeg.

Usage:
    python3 encode.py [fps] [out_name]
    (default: 30fps, output/route_growth.mp4)
"""
import pathlib
import shutil
import subprocess
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent


def main():
    fps = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    out_name = sys.argv[2] if len(sys.argv) > 2 else "route_growth.mp4"
    if not out_name.endswith(".mp4"):
        out_name += ".mp4"
    out = BASE / "output" / out_name
    out.parent.mkdir(exist_ok=True)

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        sys.exit("ffmpeg not found — install it (brew install ffmpeg) or add it to PATH")

    if not (BASE / "frames" / "frame_00000.png").exists():
        sys.exit("No frames found — run capture.py first")

    cmd = [
        ffmpeg, "-y",
        "-framerate", str(fps),
        "-i", str(BASE / "frames" / "frame_%05d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "medium",
        "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
