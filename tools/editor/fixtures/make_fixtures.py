#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate binary fixtures for the 10s editor pipeline test (Issue #5 step 1).

Creates (gitignored — regenerate with this script):
  fixtures/assets_test/scenes/test_*.png   1920x1080 flat scene backgrounds
  fixtures/assets_test/overlay/*.png       transparent character layers
  fixtures/mix_test.wav                    12.0s stereo pad (stand-in mix)

Static (committed) inputs live next to it:
  fixtures/script_test.json   mock 10-scene script (schema example)
  fixtures/timing_test.json   matching timing (10 scenes x 1.2s = 12.0s)

Run: uv run --with pillow --with numpy python tools/editor/fixtures/make_fixtures.py
"""
from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets_test"
SCENES = ASSETS / "scenes"
OVERLAY = ASSETS / "overlay"

W, H = 1920, 1080
GROUND_Y = 820


def lerp(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def gradient(img, top, bottom):
    d = ImageDraw.Draw(img)
    for yy in range(H):
        d.line([(0, yy), (W, yy)], fill=lerp(top, bottom, yy / H))


def hills(d, base_y, color, amp=90, seed_off=0.0):
    pts = [(0, base_y)]
    for xx in range(0, W + 1, 64):
        pts.append((xx, base_y - amp * (0.55 + 0.45 * math.sin(xx / 420.0 + seed_off))))
    pts += [(W, H), (0, H)]
    d.polygon(pts, fill=color)


def scene_opening(variant: int) -> Image.Image:
    img = Image.new("RGB", (W, H))
    top = (126, 197, 232) if variant == 0 else (108, 186, 226)
    bot = (223, 241, 247) if variant == 0 else (206, 236, 244)
    gradient(img, top, bot)
    d = ImageDraw.Draw(img)
    sun_x = 1500 if variant == 0 else 380
    d.ellipse([sun_x - 90, 120 - 90, sun_x + 90, 120 + 90], fill=(245, 185, 66))
    hills(d, GROUND_Y, (90, 164, 108) if variant == 0 else (104, 172, 116), seed_off=variant)
    d.rectangle([0, GROUND_Y + 120, W, H], fill=(201, 163, 107))
    # school building
    bx = 380 if variant == 0 else 1150
    d.rectangle([bx, GROUND_Y - 190, bx + 560, GROUND_Y + 130], fill=(255, 253, 247))
    d.rectangle([bx, GROUND_Y - 190, bx + 560, GROUND_Y - 150], fill=(43, 74, 139))
    for r in range(2):
        for c in range(5):
            d.rectangle([bx + 40 + c * 104, GROUND_Y - 120 + r * 100,
                         bx + 116 + c * 104, GROUND_Y - 60 + r * 100],
                        fill=(126, 200, 227))
    d.rectangle([bx + 240, GROUND_Y + 30, bx + 320, GROUND_Y + 130], fill=(90, 74, 61))
    return img


def scene_story(variant: int) -> Image.Image:
    img = Image.new("RGB", (W, H))
    if variant == 0:  # Jomon forest
        gradient(img, (142, 201, 190), (222, 240, 228))
    else:  # Yayoi paddies
        gradient(img, (150, 208, 220), (230, 244, 234))
    d = ImageDraw.Draw(img)
    hills(d, GROUND_Y - 40, (74, 138, 92), amp=110, seed_off=1.0 + variant)
    d.rectangle([0, GROUND_Y + 80, W, H], fill=(138, 111, 77))
    if variant == 0:  # pit house
        cx = 1250
        d.pieslice([cx - 260, GROUND_Y + 20, cx + 260, GROUND_Y + 340],
                   180, 360, fill=(155, 106, 62))
        d.rectangle([cx - 190, GROUND_Y + 110, cx + 190, GROUND_Y + 170],
                    fill=(120, 79, 46))
        d.rectangle([cx - 60, GROUND_Y + 170, cx + 60, GROUND_Y + 250],
                    fill=(90, 60, 38))
    else:  # rice paddies + raised storehouse
        for r in range(3):
            yy = GROUND_Y + 90 + r * 70
            for c in range(6):
                x0 = 90 + c * 300 + (r % 2) * 60
                d.rectangle([x0, yy, x0 + 240, yy + 50], fill=(96, 148, 172))
        sx = 1450
        d.rectangle([sx, GROUND_Y - 150, sx + 300, GROUND_Y - 20], fill=(199, 162, 115))
        d.polygon([(sx - 30, GROUND_Y - 150), (sx + 330, GROUND_Y - 150),
                   (sx + 150, GROUND_Y - 250)], fill=(120, 79, 46))
    return img


def scene_points(variant: int) -> Image.Image:
    img = Image.new("RGB", (W, H), (242, 227, 194) if variant == 0 else (247, 238, 210))
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 160, W, H], fill=(201, 163, 107))
    d.line([(140, 500), (W - 140, 500)], fill=(43, 74, 139), width=14)
    xs = [320, 700, 1080, 1460] if variant == 0 else [420, 900, 1380]
    for i, cx in enumerate(xs):
        d.ellipse([cx - 56, 444, cx + 56, 556], fill=(232, 84, 63))
        d.ellipse([cx - 30, 470, cx + 30, 530], fill=(255, 253, 247))
        d.line([(cx, 556), (cx, 660)], fill=(43, 74, 139), width=8)
        d.rounded_rectangle([cx - 130, 660, cx + 130, 740], 24,
                            fill=(255, 253, 247), outline=(43, 74, 139), width=6)
    return img


def scene_quiz(variant: int) -> Image.Image:
    img = Image.new("RGB", (W, H))
    gradient(img, (34, 38, 66) if variant == 0 else (48, 36, 74), (24, 26, 46))
    d = ImageDraw.Draw(img)
    for cx, col in ((420, (245, 185, 66)), (1500, (126, 200, 227))):
        d.polygon([(cx - 260, 0), (cx + 260, 0), (cx + 420, H), (cx - 420, H)],
                  fill=tuple(int(c * 0.35 + 24) for c in col))
    d.rectangle([0, GROUND_Y + 60, W, H], fill=(58, 48, 78) if variant == 0 else (44, 52, 84))
    d.line([(0, GROUND_Y + 60), (W, GROUND_Y + 60)], fill=(245, 185, 66), width=10)
    # big "?" mark: circle + hook
    qx = 960
    d.ellipse([qx - 130, 300, qx + 130, 560], outline=(255, 253, 247), width=26)
    d.rectangle([qx - 18, 560, qx + 18, 640], fill=(255, 253, 247))
    d.ellipse([qx - 22, 670, qx + 22, 714], fill=(232, 84, 63))
    return img


def scene_ending(variant: int) -> Image.Image:
    img = Image.new("RGB", (W, H))
    if variant == 0:
        gradient(img, (244, 154, 89), (250, 216, 158))
    else:
        gradient(img, (232, 120, 108), (250, 205, 150))
    d = ImageDraw.Draw(img)
    d.ellipse([960 - 140, 380 - 140, 960 + 140, 380 + 140], fill=(255, 236, 190))
    hills(d, GROUND_Y, (96, 74, 96) if variant == 0 else (84, 64, 92), amp=120,
          seed_off=2.0 + variant)
    d.rectangle([0, GROUND_Y + 130, W, H], fill=(70, 54, 76))
    return img


def character(kind: str) -> Image.Image:
    img = Image.new("RGBA", (450, 700), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    skin = (250, 224, 195)
    if kind == "sensei":     # navy suit + yellow tie + glasses
        suit, hair, tie = (43, 74, 139), (60, 54, 60), (245, 185, 66)
    else:                    # white tee + red vest
        suit, hair, tie = (255, 253, 247), (46, 42, 48), (232, 84, 63)
    # legs
    d.rounded_rectangle([150, 520, 210, 660], 24, fill=(52, 48, 58))
    d.rounded_rectangle([240, 520, 300, 660], 24, fill=(52, 48, 58))
    # body
    d.rounded_rectangle([95, 300, 355, 560], 60, fill=suit)
    if kind != "sensei":
        d.rounded_rectangle([95, 300, 165, 560], 40, fill=tie)   # vest sides
        d.rounded_rectangle([285, 300, 355, 560], 40, fill=tie)
    else:
        d.rectangle([212, 310, 238, 430], fill=tie)
    # arms
    d.rounded_rectangle([40, 320, 100, 520], 30, fill=suit)
    d.rounded_rectangle([350, 320, 410, 520], 30, fill=suit)
    # head
    d.ellipse([130, 60, 320, 300], fill=skin)
    d.pieslice([118, 30, 332, 240], 160, 380, fill=hair)
    d.ellipse([150, 150, 210, 200], fill=(255, 255, 255))
    d.ellipse([240, 150, 300, 200], fill=(255, 255, 255))
    d.ellipse([168, 162, 196, 190], fill=(40, 38, 44))
    d.ellipse([254, 162, 282, 190], fill=(40, 38, 44))
    d.arc([190, 210, 260, 260], 15, 165, fill=(150, 90, 80), width=10)
    if kind == "sensei":
        d.rounded_rectangle([138, 138, 222, 212], 18, outline=(30, 30, 36), width=8)
        d.rounded_rectangle([228, 138, 312, 212], 18, outline=(30, 30, 36), width=8)
        d.line([(222, 172), (228, 172)], fill=(30, 30, 36), width=8)
    else:  # cheeks
        d.ellipse([150, 214, 190, 240], fill=(240, 150, 140))
        d.ellipse([262, 214, 302, 240], fill=(240, 150, 140))
    return img


def mix_wav(path: Path, seconds: float = 12.0, rate: int = 48000) -> None:
    t = np.linspace(0.0, seconds, int(rate * seconds), endpoint=False)
    pad = np.zeros_like(t)
    for f, a in ((261.63, 0.30), (329.63, 0.24), (392.0, 0.20), (523.25, 0.12)):
        pad += a * np.sin(2 * np.pi * f * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * t))
    env = np.clip(np.minimum(t / 1.2, (seconds - t) / 1.5), 0.0, 1.0)
    mono = pad * env * 0.32
    stereo = np.stack([mono, mono * 0.96], axis=1)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm.tobytes())


def main() -> None:
    SCENES.mkdir(parents=True, exist_ok=True)
    OVERLAY.mkdir(parents=True, exist_ok=True)
    builders = {"opening": scene_opening, "story": scene_story,
                "points": scene_points, "quiz": scene_quiz,
                "ending": scene_ending}
    for sec, fn in builders.items():
        for v in (0, 1):
            fn(v).save(SCENES / f"test_{sec}_{'ab'[v]}.png")
            print(f"scene  test_{sec}_{'ab'[v]}.png")
    character("sensei").save(OVERLAY / "char_sensei.png")
    character("manabu").save(OVERLAY / "char_manabu.png")
    print("overlay char_sensei.png / char_manabu.png")
    mix_wav(HERE / "mix_test.wav")
    print("mix_test.wav (12.0s)")
    print("done ->", ASSETS)


if __name__ == "__main__":
    main()
