#!/usr/bin/env python3
"""Capture the route-growth animation frame by frame with Playwright.

Usage:
    python3 capture.py [frames] [fps]        # default 450 @ 30 = 15 s

Serves web/index.html locally, opens it in headless Chrome, and screenshots one
frame per step of window.setProgress(0..1). Frames go to ./frames/.
"""
import http.server
import os
import pathlib
import shutil
import socketserver
import sys
import threading
import time

from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent.parent
PORT = 8765
W, H = 1920, 1080          # output resolution
TILE_SETTLE_MS = 4000      # wait for map tiles before the first shot


def find_chromium():
    """Find a cached Chrome for Testing binary (used when the Playwright
    browser isn't installed but a manual Chromium cache exists)."""
    env = os.environ.get("CHROMIUM_PATH")
    if env:
        return env
    cache = pathlib.Path.home() / "Library/Caches/ms-playwright"
    if cache.is_dir():
        hits = sorted(
            (
                d / "chrome-mac-arm64"
                / "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
                for d in cache.glob("chromium-*")
            ),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
        )
        if hits:
            return str(hits[-1])
    return None


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(web):
    os.chdir(web)
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), QuietHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    frames = int(sys.argv[1]) if len(sys.argv) > 1 else 450
    fps = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    index = BASE / "web" / "index.html"
    if not index.exists():
        sys.exit(f"{index} not found — run prepare_web.py first")

    frames_dir = BASE / "frames"
    frames_dir.mkdir(exist_ok=True)
    for f in frames_dir.glob("*.png"):
        f.unlink()

    httpd = serve(BASE / "web")
    errors = []
    exe = find_chromium() if not shutil.which("playwright") else None

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        except Exception:
            browser = p.chromium.launch(executable_path=find_chromium())
        page = browser.new_page(viewport={"width": W, "height": H})
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load", timeout=60000)
        try:
            page.wait_for_function("window.__mapReady===true", timeout=60000)
        except Exception:
            print("Map never became ready — Amap JS API failed to load/authenticate.")
            for e in set(errors):
                print("  page error:", e[:240])
            browser.close()
            sys.exit(1)

        page.wait_for_timeout(TILE_SETTLE_MS)
        page.evaluate("setProgress(0)")
        page.wait_for_timeout(300)

        t0 = time.time()
        for i in range(frames):
            page.evaluate(f"setProgress({i / (frames - 1):.6f})")
            page.wait_for_timeout(30)
            page.screenshot(path=str(frames_dir / f"frame_{i:05d}.png"))
        dt = time.time() - t0
        print(f"captured {frames} frames in {dt:.0f}s -> {frames_dir}")
        browser.close()

    errs = set(errors)
    if errs:
        print("page console errors:")
        for e in list(errs)[:5]:
            print("  -", e[:200])


if __name__ == "__main__":
    main()
