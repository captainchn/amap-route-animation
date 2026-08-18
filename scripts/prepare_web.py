#!/usr/bin/env python3
"""Inject route data into the render page -> web/index.html.

Usage:
    python3 prepare_web.py [route.json]

Requires AMAP_KEY (Amap JS API key) via environment variable — it is injected
into the page so the map can load.
"""
import json
import os
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent

KEY = os.environ.get("AMAP_KEY")
if not KEY:
    sys.exit(
        "AMAP_KEY environment variable not set.\n"
        "Get a free JS API key at https://console.amap.com/ then: export AMAP_KEY=your_key"
    )


def main():
    route_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "route.json"
    if not route_path.exists():
        sys.exit(f"route file not found: {route_path} (run fetch_route.py first)")

    route = json.loads(route_path.read_text(encoding="utf-8"))
    tpl = (BASE / "web" / "render_template.html").read_text(encoding="utf-8")

    html = (
        tpl.replace("__AMAP_KEY__", KEY)
        .replace("__ROUTE_JSON__", json.dumps(route, ensure_ascii=False))
    )
    out = BASE / "web" / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
