#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

demo = Path("/home/marctheshark/Documents/the-grid/agent-body-protocol/docs/demo")
frames = demo / "frames"
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = ImageFont.truetype(font_path, 52)
small = ImageFont.truetype(font_path, 26)


def card(name: str, title: str, sub: str) -> None:
    img = Image.new("RGB", (1280, 720), (16, 18, 22))
    draw = ImageDraw.Draw(img)
    draw.text((80, 250), title, fill=(240, 236, 228), font=font)
    draw.text((80, 340), sub, fill=(170, 168, 160), font=small)
    img.save(frames / name)


card("00-title.png", "Agent Body Protocol", "Coding-agent events in. Lamp body language out.")
card("08-end.png", "USB-C into HAL they shipped", "github.com/marctheshark3/agent-body-protocol")

beats = [
    ("00-title.png", 3.2),
    ("01-idle.png", 2.8),
    ("02-ci-pass.png", 3.6),
    ("03-ring.png", 3.2),
    ("04-in-call.png", 2.8),
    ("05-dance.png", 3.6),
    ("08-end.png", 3.2),
]
clips = []
for i, (name, sec) in enumerate(beats):
    clip = demo / f"clip{i:02d}.mp4"
    n = int(round(sec * 30))
    vf = f"scale=1280:720,format=yuv420p,zoompan=z='min(1.04,1+0.0008*on)':d={n}:s=1280x720:fps=30"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(frames / name),
            "-vf",
            vf,
            "-frames:v",
            str(n),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(clip),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    clips.append(clip)
    print("clip", clip.name, n)

lst = demo / "clips.txt"
lst.write_text("".join(f"file '{c.name}'\n" for c in clips))
concat = demo / "video-silent.mp4"
subprocess.run(
    [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(lst),
        "-c",
        "copy",
        str(concat),
    ],
    check=True,
    cwd=demo,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
final = demo / "abp-lab-demo.mp4"
subprocess.run(
    [
        "ffmpeg",
        "-y",
        "-i",
        str(concat),
        "-i",
        str(demo / "vo.mp3"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(final),
    ],
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
print("wrote", final, final.stat().st_size)
