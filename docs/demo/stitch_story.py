#!/usr/bin/env python3
from pathlib import Path
import subprocess

demo = Path("/home/marctheshark/Documents/the-grid/agent-body-protocol/docs/demo")
story = demo / "story"
vo = demo / "vo-story.mp3"
# timed to the 98s VO
beats = [
    ("01-hook.png", 12.0),
    ("02-gap.png", 8.0),
    ("03-stack.png", 9.0),
    ("04-language.png", 17.0),
    ("05a-ci-think.png", 5.0),
    ("05-ci.png", 6.0),
    ("06-perm.png", 8.0),
    ("07-help.png", 9.0),
    ("08-exam.png", 8.0),
    ("09-future.png", 7.0),
    ("10-end.png", 4.6),
]
clips = []
for i, (name, sec) in enumerate(beats):
    clip = demo / f"sclip{i:02d}.mp4"
    n = int(round(sec * 30))
    subprocess.run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", str(story / name),
            "-vf", f"scale=1280:720,format=yuv420p,zoompan=z='min(1.03,1+0.0004*on)':d={n}:s=1280x720:fps=30",
            "-frames:v", str(n), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(clip),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    clips.append(clip)
    print(clip.name, n)
lst = demo / "sclips.txt"
lst.write_text("".join(f"file '{c.name}'\n" for c in clips))
silent = demo / "story-silent.mp4"
subprocess.run(
    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)],
    check=True, cwd=demo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
pad = demo / "story-pad.mp4"
subprocess.run(
    ["ffmpeg", "-y", "-i", str(silent), "-vf", "tpad=stop_mode=clone:stop_duration=8",
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(pad)],
    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
final = demo / "abp-story.mp4"
subprocess.run(
    ["ffmpeg", "-y", "-i", str(pad), "-i", str(vo), "-c:v", "libx264", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(final)],
    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
print("final", final, final.stat().st_size)
