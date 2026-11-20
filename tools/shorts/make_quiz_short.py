#!/usr/bin/env python3
"""Build a native vertical (1080x1920) quiz Short for アニメ日本史ラボ.

Re-renders one quiz scene from an episode in a vertical layout:
full-canvas chalkboard, big question/choices, Sensei+Manabu sprites at
the bottom, per-beat subtitles, answer row highlighted (yamabuki +
red check) from the beat where Manabu answers. Audio is cut from the
episode's FINAL_v2 render so voices/timing match the main video.

Usage (run on the Mac mini inside the repo):
  python3 tools/shorts/make_quiz_short.py --episode ep01 --quiz 1 \
      --video video/ep01_FINAL_v2.mp4 \
      --out video/shorts/ep01_short_quiz1_v2.mp4
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
FONT_DIR = Path("/Library/Fonts")
FONTS = {"Black": "NotoSansJP-Black.otf", "Bold": "NotoSansJP-Bold.otf",
         "Regular": "NotoSansJP-Regular.otf"}

W, H = 1080, 1920
SS = 2  # supersampling
AI = (43, 74, 139)
SHU = (232, 84, 63)
YAMABUKI = (245, 185, 66)
WHITE = (255, 253, 247)
DARK = (38, 40, 46)
BOARD = (39, 82, 68)
BOARD_ROW = (52, 102, 86)
WOOD = (122, 84, 50)
WOOD_DARK = (94, 63, 36)

LABELS = ["ア", "イ", "ウ"]


def font(kind, size):
    return ImageFont.truetype(str(FONT_DIR / FONTS[kind]), size * SS)


def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=fnt) <= max_w * SS or not cur:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def paste_sprite(canvas, path, height, cx, bottom, opacity=1.0):
    sp = Image.open(path).convert("RGBA")
    scale = (height * SS) / sp.height
    sp = sp.resize((int(sp.width * scale), height * SS),
                   Image.LANCZOS)
    if opacity < 1.0:
        a = sp.getchannel("A").point(lambda v: int(v * opacity))
        sp.putalpha(a)
    x = int(cx * SS - sp.width / 2)
    y = int(bottom * SS - sp.height)
    canvas.alpha_composite(sp, (x, y))


def draw_frame(state, quiz, ep_label, quiz_no, subtitle, speaker,
               highlight):
    """state: 'intro' | 'question'. highlight: answer idx or None."""
    img = Image.new("RGBA", (W * SS, H * SS), BOARD + (255,))
    d = ImageDraw.Draw(img, "RGBA")

    # wooden frame
    d.rectangle([0, 0, W * SS, H * SS], fill=WOOD + (255,))
    d.rectangle([18 * SS, 18 * SS, (W - 18) * SS, (H - 18) * SS],
                fill=WOOD_DARK + (255,))
    d.rectangle([34 * SS, 34 * SS, (W - 34) * SS, (H - 34) * SS],
                fill=BOARD + (255,))

    # header
    d.text((W * SS / 2, 108 * SS), "日本史クイズ",
           font=font("Black", 92), anchor="mm", fill=WHITE,
           stroke_width=3 * SS, stroke_fill=DARK)
    d.text((W * SS / 2, 208 * SS), ep_label,
           font=font("Bold", 40), anchor="mm", fill=YAMABUKI)

    if state == "intro":
        d.text((W * SS / 2, 700 * SS), "クイズタイム！",
               font=font("Black", 128), anchor="mm", fill=WHITE,
               stroke_width=3 * SS, stroke_fill=DARK)
        d.text((W * SS / 2, 880 * SS), f"第{quiz_no}問",
               font=font("Black", 96), anchor="mm", fill=YAMABUKI,
               stroke_width=3 * SS, stroke_fill=DARK)
    else:
        # question
        qf = font("Bold", 63)
        lines = wrap(d, quiz["q"], qf, 900)
        y = 330 * SS
        for ln in lines:
            d.text((W * SS / 2, y), ln, font=qf, anchor="ma",
                   fill=WHITE, stroke_width=2 * SS, stroke_fill=DARK)
            y += 92 * SS
        # choices
        row_y = 730
        cf = font("Bold", 62)
        lf = font("Black", 62)
        for i, ch in enumerate(quiz["choices"]):
            top = row_y * SS
            bot = (row_y + 168) * SS
            hl = (highlight == i)
            fill = YAMABUKI if hl else BOARD_ROW
            d.rounded_rectangle([64 * SS, top, (W - 64) * SS, bot],
                                radius=28 * SS, fill=fill + (255,))
            tc = DARK if hl else WHITE
            d.text((120 * SS, (row_y + 84) * SS), LABELS[i], font=lf,
                   anchor="lm", fill=tc)
            d.text((215 * SS, (row_y + 84) * SS), ch, font=cf,
                   anchor="lm", fill=tc)
            if hl:
                cx, cy, r = (W - 150) * SS, (row_y + 84) * SS, 52 * SS
                d.ellipse([cx - r, cy - r, cx + r, cy + r],
                          outline=SHU + (255,), width=10 * SS)
                d.text((cx, cy - 4 * SS), "✓", font=font("Black", 64),
                       anchor="mm", fill=SHU)
            row_y += 208

    # characters (speaker full opacity, other slightly faded)
    sprites = REPO / "assets/characters_v2/sprites"
    paste_sprite(img, sprites / "char_manabu.png", 500, 235, 1908,
                 1.0 if speaker == "manabu" else 0.72)
    paste_sprite(img, sprites / "char_sensei.png", 585, 845, 1908,
                 1.0 if speaker == "sensei" else 0.72)

    # subtitle bar
    d.rounded_rectangle([36 * SS, 1690 * SS, (W - 36) * SS, 1852 * SS],
                        radius=24 * SS, fill=(0, 0, 0, 150))
    name = "マナブ" if speaker == "manabu" else "先生"
    d.text((64 * SS, 1722 * SS), name, font=font("Black", 38),
           anchor="la", fill=YAMABUKI)
    sf = font("Bold", 44)
    lines = wrap(d, subtitle, sf, 920)[:2]
    y = 1770 * SS
    for ln in lines:
        d.text((W * SS / 2, y), ln, font=sf, anchor="ma", fill=WHITE)
        y += 58 * SS

    return img.resize((W, H), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True)
    ap.add_argument("--quiz", type=int, required=True, help="1-based")
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ep-label", default="")
    args = ap.parse_args()

    ep = args.episode
    script = json.loads(
        (REPO / f"content/episodes/{ep}/script.json").read_text())
    quiz = script["quiz"][args.quiz - 1]
    timing = json.loads(
        (REPO / f"audio/{ep}/timing_unified.json").read_text())
    scenes = timing if isinstance(timing, list) else timing["scenes"]
    quiz_scenes = [s for s in scenes if s.get("section") == "quiz"]
    scene = quiz_scenes[args.quiz - 1]
    beats = scene["beats"]
    seg_start = max(0.0, scene["start"] - 0.2)
    last = beats[-1]
    seg_end = last["start"] + last["duration"] + 0.35
    seg_dur = seg_end - seg_start

    # answer beat = first manabu beat in the scene
    ans_beat = next(i for i, b in enumerate(beats)
                    if b["speaker"] == "manabu")

    label = args.ep_label or f"{ep.upper()} のクイズコーナーから出題"
    tmp = Path(tempfile.mkdtemp())
    frames = []
    for i, b in enumerate(beats):
        state = "intro" if i == 0 else "question"
        hl = quiz["answer"] if i >= ans_beat else None
        fr = draw_frame(state, quiz, label, args.quiz, b["text"],
                        b["speaker"], hl)
        p = tmp / f"f{i}.png"
        fr.save(p)
        start = b["start"] - seg_start
        end = (beats[i + 1]["start"] - seg_start) if i + 1 < len(beats) \
            else seg_dur
        frames.append((p, end - start))

    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-ss", f"{seg_start:.3f}", "-i",
           str(REPO / args.video)]
    for p, dur in frames:
        cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(p)]
    n = len(frames)
    filt = "".join(f"[{i + 1}:v]" for i in range(n)) + \
        f"concat=n={n}:v=1:a=0,fps=30,format=yuv420p[v]"
    cmd += ["-filter_complex", filt, "-map", "[v]", "-map", "0:a",
            "-t", f"{seg_dur:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:])
        sys.exit(1)
    print("OK", out, f"{seg_dur:.1f}s")


if __name__ == "__main__":
    main()
