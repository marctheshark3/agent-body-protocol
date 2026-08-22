#!/usr/bin/env python3
from pathlib import Path
import subprocess

demo = Path("/home/marctheshark/Documents/the-grid/agent-body-protocol/docs/demo")
receipts = demo / "receipts"
vo = demo / "vo-proof.mp3"
beats = [
    (demo / "frames" / "00-title.png", 3.0),
    (receipts / "tests_passed.png", 5.2),
    (receipts / "look.png", 5.2),
    (receipts / "follow.png", 4.6),
    (receipts / "dance.png", 4.6),
    (demo / "frames" / "08-end.png", 3.4),
]
clips = []
for i, (src, sec) in enumerate(beats):
    clip = demo / f"pclip{i:02d}.mp4"
    n = int(round(sec * 30))
    subprocess.run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", str(src),
            "-vf", f"scale=1280:720,format=yuv420p,zoompan=z=1:d={n}:s=1280x720:fps=30",
            "-frames:v", str(n), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(clip),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    clips.append(clip)
lst = demo / "pclips.txt"
lst.write_text("".join(f"file '{c.name}'\n" for c in clips))
silent = demo / "proof-silent.mp4"
subprocess.run(
    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)],
    check=True, cwd=demo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
# pad video to cover VO
pad = demo / "proof-pad.mp4"
subprocess.run(
    ["ffmpeg", "-y", "-i", str(silent), "-vf", "tpad=stop_mode=clone:stop_duration=6",
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(pad)],
    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
final = demo / "abp-proof.mp4"
subprocess.run(
    ["ffmpeg", "-y", "-i", str(pad), "-i", str(vo), "-c:v", "libx264", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(final)],
    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
print(final, final.stat().st_size)
