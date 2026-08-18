#!/usr/bin/env bash
# One-command pipeline: place names -> route-growth animation mp4
#
# Usage:
#   ./run.sh "起点" "终点" [输出文件名]
#   FRAMES=900 FPS=30 ./run.sh "海口" "拉萨" haikou_lasa
#
# Requires: AMAP_KEY env var, python3 + playwright, ffmpeg (see README).
set -euo pipefail

ORIGIN="${1:?usage: ./run.sh \"起点\" \"终点\" [输出名]}"
DEST="${2:?usage: ./run.sh \"起点\" \"终点\" [输出名]}"
NAME="${3:-route_growth}"
FRAMES="${FRAMES:-450}"
FPS="${FPS:-30}"

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "▶ [1/4] fetch route: $ORIGIN → $DEST"
python3 scripts/fetch_route.py "$ORIGIN" "$DEST" route.json

echo "▶ [2/4] prepare render page"
python3 scripts/prepare_web.py route.json

echo "▶ [3/4] capture ${FRAMES} frames @ ${FPS}fps"
python3 scripts/capture.py "$FRAMES" "$FPS"

echo "▶ [4/4] encode video"
python3 scripts/encode.py "$FPS" "$NAME"

echo "✅ done: output/$NAME.mp4"
