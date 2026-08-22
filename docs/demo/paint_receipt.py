#!/usr/bin/env python3
"""Paint 1280x720 receipt cards from live HAL proof JSON."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

JOINTS = (
    "base_yaw.pos",
    "base_pitch.pos",
    "elbow_pitch.pos",
    "wrist_pitch.pos",
    "wrist_roll.pos",
)


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    raw = (value or "#000000").lstrip("#")
    if len(raw) != 6:
        return (20, 22, 26)
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def paint(row: dict, dest: Path) -> Path:
    img = Image.new("RGB", (1280, 720), (11, 13, 17))
    draw = ImageDraw.Draw(img)
    title = _font(36)
    body = _font(22)
    mono = _font(20)
    small = _font(16)
    ok = bool((row.get("grade") or {}).get("ok"))
    badge = "PASS" if ok else "FAIL"
    badge_color = (61, 214, 140) if ok else (255, 107, 107)
    draw.text((48, 28), f"ABP proof  ·  {row.get('name')}", fill=(242, 238, 230), font=title)
    draw.rounded_rectangle((1040, 28, 1232, 78), 12, fill=badge_color)
    draw.text((1068, 38), badge, fill=(11, 13, 17), font=body)
    draw.text((48, 82), (row.get("grade") or {}).get("reason") or "", fill=(170, 168, 160), font=small)

    hex_after = row.get("led_after") or "#000000"
    draw.rounded_rectangle((48, 120, 300, 280), 16, fill=_hex_to_rgb(hex_after))
    draw.text((48, 292), f"LED {row.get('led_before') or '—'} → {hex_after}", fill=(242, 238, 230), font=mono)

    y = 120
    draw.text((340, y), "joint                  before     after      Δ°", fill=(139, 149, 161), font=mono)
    y += 36
    before = (row.get("before") or {}).get("positions") or {}
    after = (row.get("after") or {}).get("positions") or {}
    deltas = row.get("deltas") or {}
    for name in JOINTS:
        deg = float(deltas.get(name) or 0)
        color = (255, 208, 137) if deg >= 5 else (200, 204, 210)
        label = name.replace(".pos", "")
        line = f"{label:<18} {float(before.get(name) or 0):7.1f}  {float(after.get(name) or 0):7.1f}  {deg:6.1f}"
        draw.text((340, y), line, fill=color, font=mono)
        y += 32

    markers = "  ".join(row.get("markers") or [])
    statuses = "  ".join(
        f"{item.get('path')} {item.get('status')}" for item in (row.get("dispatched") or [])
    )
    draw.text((48, 520), markers[:90], fill=(200, 204, 210), font=small)
    draw.text((48, 552), f"HAL {statuses}", fill=(242, 238, 230), font=mono)
    draw.text((48, 600), "Source: live GET /led/color + GET /servo/position on HAL_SIMULATE :5001", fill=(139, 149, 161), font=small)
    draw.text((48, 632), "Not official CAD iframe. Not Isaac. HTTP 200 alone is not a pass.", fill=(139, 149, 161), font=small)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest)
    return dest


def main() -> int:
    import sys

    src = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    paint(json.loads(src.read_text()), dest)
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
