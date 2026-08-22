#!/usr/bin/env python3
"""Themed 1280x720 story frames for the ABP concept video."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path("/home/marctheshark/Documents/the-grid/agent-body-protocol/docs/demo/story")
BG = (11, 13, 17)
INK = (242, 238, 230)
MUTED = (158, 164, 172)
GOLD = (255, 208, 137)

EVENTS = [
    ("started", (48, 48, 48), "dim white", "silent"),
    ("thinking", (0, 80, 255), "slow blue", "silent"),
    ("waiting_for_user", (255, 150, 0), "amber pulse", "looks at you"),
    ("permission_required", (255, 150, 0), "amber", "asks once"),
    ("blocked", (255, 0, 0), "red breath", "Want help?"),
    ("tests_passed", (0, 200, 80), "green", "two words"),
    ("tests_failed", (255, 0, 0), "red flash", "two words"),
    ("completed", (0, 200, 80), "green flourish", "short wiggle"),
    ("quiet", (42, 48, 56), "restore", "light only"),
]


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)


def card() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (1280, 720), BG)
    return img, ImageDraw.Draw(img)


def save(img: Image.Image, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / name
    img.save(dest)
    return dest


def title() -> None:
    img, d = card()
    d.text((64, 180), "Software has a life cycle.", fill=INK, font=font(44))
    d.text((64, 250), "Hardware does not.", fill=GOLD, font=font(44))
    d.text((64, 360), "Agent Body Protocol", fill=INK, font=font(28))
    d.text((64, 410), "Coding-agent events in. Lamp body language out.", fill=MUTED, font=font(22))
    save(img, "01-hook.png")


def missing() -> None:
    img, d = card()
    d.text((64, 80), "Today the life cycle is a terminal.", fill=INK, font=font(34))
    lines = [
        "started",
        "thinking",
        "waiting",
        "permission",
        "blocked",
        "tests passed / failed",
        "completed",
    ]
    y = 170
    for line in lines:
        d.ellipse((70, y + 8, 86, y + 24), fill=GOLD)
        d.text((110, y), line, fill=INK, font=font(26))
        y += 52
    d.text((64, 640), "The Lamp has no word for any of this. That is the gap.", fill=MUTED, font=font(20))
    save(img, "02-gap.png")


def cable() -> None:
    img, d = card()
    d.text((64, 70), "The missing cable", fill=GOLD, font=font(22))
    layers = [
        ("Brain", "any coding agent, or CI"),
        ("Protocol", "nine events + four verbs"),
        ("Body", "lights, look, dance, follow"),
        ("World", "simulator today · real lamp later"),
    ]
    y = 140
    for title_s, sub in layers:
        d.rounded_rectangle((64, y, 1216, y + 100), 16, fill=(20, 24, 30), outline=(42, 49, 58))
        d.text((88, y + 18), title_s, fill=GOLD, font=font(24))
        d.text((88, y + 54), sub, fill=INK, font=font(22))
        y += 120
    save(img, "03-stack.png")


def language() -> None:
    img, d = card()
    d.text((64, 36), "The language is light and pose", fill=INK, font=font(32))
    d.text((64, 86), "Quiet by default. Night mode = light only.", fill=MUTED, font=font(18))
    cols = 3
    w, h = 360, 150
    for i, (name, color, how, note) in enumerate(EVENTS):
        x = 64 + (i % cols) * (w + 24)
        y = 140 + (i // cols) * (h + 18)
        d.rounded_rectangle((x, y, x + w, y + h), 14, fill=(20, 24, 30), outline=(42, 49, 58))
        d.rounded_rectangle((x + 16, y + 18, x + 70, y + 72), 10, fill=color)
        d.text((x + 86, y + 20), name, fill=INK, font=font(18))
        d.text((x + 86, y + 52), how, fill=GOLD, font=font(16))
        d.text((x + 86, y + 84), note, fill=MUTED, font=font(16))
    save(img, "04-language.png")


def scene(name: str, filename: str, human: str, lamp: str, color: tuple[int, int, int], footer: str) -> None:
    img, d = card()
    d.text((64, 40), name, fill=GOLD, font=font(22))
    d.rounded_rectangle((64, 110, 600, 300), 18, fill=(28, 24, 18), outline=(90, 70, 30))
    d.text((88, 130), "Human", fill=GOLD, font=font(16))
    d.text((88, 170), human, fill=INK, font=font(26))
    d.rounded_rectangle((680, 110, 1216, 300), 18, fill=(20, 24, 30), outline=(42, 49, 58))
    d.ellipse((710, 160, 810, 260), fill=color)
    d.text((840, 150), "Lamp", fill=GOLD, font=font(16))
    d.text((840, 190), lamp, fill=INK, font=font(24))
    d.text((64, 380), footer, fill=INK, font=font(26))
    d.text((64, 640), "Color and pose. Not a chat bubble on the lamp.", fill=MUTED, font=font(18))
    save(img, filename)


def exam() -> None:
    img, d = card()
    d.text((64, 50), "The joints are the exam", fill=INK, font=font(36))
    rows = [
        ("look", "head tips toward you", "wrist 0° → −85°"),
        ("dance", "four joints move", "a short celebration"),
        ("follow", "needs a person in view", "without one, it says it cannot"),
    ]
    y = 160
    for title_s, a, b in rows:
        d.rounded_rectangle((64, y, 1216, y + 130), 16, fill=(20, 24, 30), outline=(42, 49, 58))
        d.text((88, y + 24), title_s, fill=GOLD, font=font(28))
        d.text((360, y + 28), a, fill=INK, font=font(26))
        d.text((360, y + 74), b, fill=MUTED, font=font(22))
        y += 150
    save(img, "08-exam.png")


def future() -> None:
    img, d = card()
    d.text((64, 50), "What people add next", fill=INK, font=font(36))
    items = [
        "Adapters for the coding agent you already use",
        "CI that turns the lamp green or red",
        "The same commands on a real lamp later",
        "New skills only if the body already has the move",
        "No second model to drive each joint",
    ]
    y = 150
    for item in items:
        d.text((64, y), "▸  " + item, fill=INK, font=font(26))
        y += 70
    d.text((64, 620), "Teach the protocol. Do not re-teach the motors.", fill=GOLD, font=font(22))
    save(img, "09-future.png")


def end() -> None:
    img, d = card()
    d.text((64, 220), "Nine events. Four verbs.", fill=INK, font=font(40))
    d.text((64, 290), "The Lamp already knows the rest.", fill=GOLD, font=font(32))
    d.text((64, 420), "github.com/marctheshark3/agent-body-protocol", fill=MUTED, font=font(22))
    save(img, "10-end.png")


def main() -> None:
    title()
    missing()
    cable()
    language()
    scene(
        "Scenario 1  ·  tests running",
        "05a-ci-think.png",
        "“run the suite”",
        "thinking",
        (0, 80, 255),
        "Slow blue. The agent is working. You do not open a dashboard.",
    )
    scene(
        "Scenario 1  ·  tests running",
        "05-ci.png",
        "“run the suite”",
        "tests_passed",
        (0, 120, 80),
        "Blue while it works. Green when it is done. No dashboard.",
    )
    scene(
        "Scenario 2  ·  permission",
        "06-perm.png",
        "“push to main”",
        "amber  ·  “Do you want to allow that?”",
        (255, 150, 0),
        "One ask. Looks at you. Not a Claude monologue.",
    )
    scene(
        "Scenario 3  ·  Help Mode",
        "07-help.png",
        "“I’m stuck on this login”",
        "red  ·  “Want help?”",
        (200, 40, 40),
        "Consent first. Point at reset. Never types a password.",
    )
    exam()
    future()
    end()
    print("wrote", len(list(OUT.glob("*.png"))), "frames")


if __name__ == "__main__":
    main()
