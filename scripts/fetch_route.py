#!/usr/bin/env python3
"""Fetch a driving route from Amap (高德地图) as GCJ-02 coordinates.

Requires the AMAP_KEY environment variable (Amap Web Service API key).

Usage:
    python3 fetch_route.py "起点" "终点" [out.json]

Origin/destination can be Chinese place names (auto-geocoded) or "lng,lat".
Output: {"start_label":..., "end_label":..., "distance_m":..., "duration_s":..., "points":[[lng,lat],...]}

The coordinates are GCJ-02 — use them directly with the Amap JS API
(map + data share the same coordinate system, so nothing drifts).
"""
import json
import os
import sys
import urllib.parse
import urllib.request

KEY = os.environ.get("AMAP_KEY")
if not KEY:
    sys.exit(
        "AMAP_KEY environment variable not set.\n"
        "Get a free key at https://console.amap.com/ then: export AMAP_KEY=your_key"
    )

GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
DRIVING_URL = "https://restapi.amap.com/v3/direction/driving"


def http_get(url, params):
    req = urllib.request.Request(
        url + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "Mozilla/5.0 (Macintosh)"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def geocode(query):
    """Return a 'lng,lat' string. Accepts coordinates or a place name."""
    q = query.strip()
    if q.count(",") == 1:  # already coordinates
        lng, lat = q.split(",")
        return f"{float(lng):.6f},{float(lat):.6f}"
    data = http_get(GEOCODE_URL, {"key": KEY, "address": q})
    if data.get("status") != "1" or not data.get("geocodes"):
        sys.exit(f"Geocode failed for {q!r}: {data.get('info')} (infocode={data.get('infocode')})")
    return data["geocodes"][0]["location"]


def decode_polyline(polyline):
    """Parse Amap's 'lng,lat;lng,lat;...' polyline string into points."""
    out = []
    for item in polyline.split(";"):
        if not item:
            continue
        parts = item.split(",")
        if len(parts) != 2:
            continue
        try:
            out.append([float(parts[0]), float(parts[1])])
        except ValueError:
            pass
    # dedupe adjacent duplicates
    res = []
    for p in out:
        if not res or res[-1] != p:
            res.append(p)
    return res


def main():
    if len(sys.argv) < 3:
        sys.exit('usage: python3 fetch_route.py "起点" "终点" [out.json]')
    origin, dest = sys.argv[1], sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else "route.json"

    oloc, dloc = geocode(origin), geocode(dest)
    print(f"origin: {origin!r} -> {oloc}")
    print(f"dest  : {dest!r} -> {dloc}")

    data = http_get(DRIVING_URL, {
        "key": KEY,
        "origin": oloc,
        "destination": dloc,
        "extensions": "all",
        "strategy": "10",
        "output": "json",
    })
    if data.get("status") != "1" or not data.get("route", {}).get("paths"):
        sys.exit(f"Route failed: {data.get('info')} (infocode={data.get('infocode')})")

    path = data["route"]["paths"][0]
    points = []
    for step in path.get("steps", []):
        points.extend(decode_polyline(step.get("polyline", "")))

    if not points:
        sys.exit("Route is empty — check that start/end are drivable")

    route = {
        "start_label": origin,
        "end_label": dest,
        "distance_m": int(path.get("distance", 0)),
        "duration_s": int(path.get("duration", 0)),
        "points": points,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(route, f, ensure_ascii=False)
    print(f"wrote {out_path}: {len(points)} points, "
          f"{route['distance_m'] / 1000:.1f} km, {route['duration_s'] / 60:.0f} min")


if __name__ == "__main__":
    main()
