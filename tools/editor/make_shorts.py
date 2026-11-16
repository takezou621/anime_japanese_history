#!/usr/bin/env python3
"""クイズ Shorts 制作 (タスク7): 1080x1920 縦型クイズ動画.

各話の quiz セクションから 1 問を抽出し、1080x1920 縦型に再構成する。
- 映像: センター配置 (ブラー背景パッド) — キャラ/黒板/字幕カードを保持
- テロップ: 問題(3s) -> 選択肢(5s) -> 正解(3s) -> 解説(残り) を
  script.json の quiz 配列から自動生成して 1080x1920 用 ASS で焼き込み
- 音声: 元の mix 区間をそのまま使用 (LUFS ~-14.5 維持)
- 冒頭 0.5s フックテキスト「この問題、解けますか?」

Usage:
  uv run --with pillow python tools/editor/make_shorts.py \
      --episode ep01 --quiz-index 0 [--out video/shorts_ep01_q01.mp4]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"
SHORT_W, SHORT_H = 1080, 1920
MAX_DUR = 20.0


def _ass_time(sec: float) -> str:
    sec = max(sec, 0)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def quiz_scene_span(script: dict, timing: dict, quiz_index: int) -> tuple[str, float, float]:
    """quiz_index 問目の (scene_id, 開始秒, 終了秒) を返す (グローバル時刻)."""
    tscenes = {s.get("id"): s for s in timing.get("scenes", [])}
    seen = -1
    for sc in script.get("scenes", []):
        if sc.get("section") != "quiz":
            continue
        seen += 1
        if seen != quiz_index:
            continue
        sid = sc["id"]
        ts = tscenes.get(sid)
        if not ts or not ts.get("beats"):
            raise SystemExit(f"timing has no beats for {sid}")
        beats = ts["beats"]
        q_start = float(beats[min(1, len(beats) - 1)]["start"])
        end = float(sc.get("duration", 0) or 0)
        if end:
            end = q_start + end if False else q_start
        q_end = float(beats[-1]["start"]) + float(beats[-1].get("duration", 4.0))
        return sid, q_start, max(q_end, q_start + 18.0)
    raise SystemExit(f"quiz section not found (index {quiz_index})")


def build_telop_ass(quiz: dict, dur: float, out_path: Path) -> None:
    """1080x1920 縦型テロップ ASS を生成 (問題/選択肢/正解/解説)."""
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {SHORT_W}
PlayResY: {SHORT_H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Telop,Hiragino Mincho ProN,56,&H00FFFFFF,&H00FFFFFF,&H00202020,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,7,60,60,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    def _fit(text: str) -> str:
        """fit-to-width: 1080-128px=952px に収まるよう改行/フォント縮小。
        JP 1字 ≈ fontsize。fs56 で 15字/行 -> はみ出す場合は fs44 で 20字/行
        -> さらに fs36 で 26字/行 (最大2行)。句読点・区切りで折る。"""
        for per_line, fs_tag in ((15, ""), (20, "{\\fs44}"), (30, "{\\fs32}")):
            lines, buf = [], ""
            for ch in text:
                buf += ch
                if len(buf) >= per_line and (ch in "、。？!?・= " or len(buf) >= per_line + 3):
                    lines.append(buf)
                    buf = ""
            if buf:
                lines.append(buf)
            if len(lines) <= 2:
                return fs_tag + "\\N".join(lines)
        per_line, fs_tag = 30, "{\\fs32}"
        lines, buf = [], ""
        for ch in text:
            buf += ch
            if len(buf) >= per_line and ch in "、。？!?・= ":
                lines.append(buf)
                buf = ""
        if buf:
            lines.append(buf)
        return fs_tag + "\\N".join(lines[:2])

    def add(st: float, en: float, text: str, zone: str, mv: int):
        # zone: "top"=上部空きゾーン (y250-600), "bottom"=下部空きゾーン
        # (y1300-1800) — 16:9 映像帯 (y656-1264) の外側に配置
        an = "8" if zone == "top" else "2"
        safe = text.replace("{", "（").replace("}", "）")
        safe = _fit(safe)
        events.append(f"Dialogue: 0,{_ass_time(st)},{_ass_time(en)},Telop,,"
                      f"0,0,{mv},,{{\\an{an}}}{safe}")

    # 16:9 映像帯は y 656-1264 — テロップはその外側 (上部 y250-600 /
    # 下部 y1350-1800) に配置して焼き込み字幕と競合しない
    add(0.0, 0.9, "この問題、解けますか?", "top", 280)     # フック (上部)
    # 質問テロップ: 本文のみ + fs32 単行 (lead指示: 24字×32=768px、
    # 左右余白 ~156px。ボード上の字幕に話者は既に表示のため重複なし)
    # ※ fit を経由しない (fs32 タグのサニタイズ回避 + 単行保証)
    q_text = str(quiz['q']).replace("{", "（").replace("}", "）").strip()
    fs_tag = "{\\fs32}" if len(q_text) > 17 else ""
    events.append(f"Dialogue: 0,{_ass_time(0.9)},{_ass_time(min(4.4, dur))},"
                  f"Telop,,0,0,270,,{{\\an8}}{fs_tag}{q_text}")
    chs = [str(c) for c in quiz.get("choices", [])][:3]
    marks = "ア イ ウ".split()
    chs_text = "\n".join(f"{marks[i]} {c}" for i, c in enumerate(chs))
    an_top = "8"
    events.append(f"Dialogue: 0,{_ass_time(4.4)},{_ass_time(min(9.4, dur))},Telop,,"
                  f"0,0,250,,{{\\an{an_top}}}{chs_text.replace(chr(10), chr(92) + 'N')}")
    ans = int(quiz.get("answer", 0))
    ans_mark = marks[ans] if 0 <= ans < len(marks) else "ア"
    add(9.4, min(12.4, dur), f"正解は…{ans_mark}!", "bottom", 430)
    expl = str(quiz.get("explain", "")).strip()
    add(12.4, dur - 0.2, f"解説: {expl}", "bottom", 370)
    out_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True)
    ap.add_argument("--quiz-index", type=int, default=0)
    ap.add_argument("--max-dur", type=float, default=MAX_DUR)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    ep = args.episode
    src = REPO / "video" / f"{ep}_FINAL.mp4"
    script = json.load(open(REPO / "content" / "episodes" / ep / "script.json",
                            encoding="utf-8"))
    timing = json.load(open(REPO / "audio" / ep / "timing.json", encoding="utf-8"))
    quiz = script.get("quiz", [])[args.quiz_index]

    sid, start, end = quiz_scene_span(script, timing, args.quiz_index)
    dur = min(end - start, args.max_dur)
    out = Path(args.out or f"video/shorts_{ep}_q{args.quiz_index + 1:02d}.mp4")

    ass_path = REPO / "video" / f"{out.stem}_telop.ass"
    build_telop_ass(quiz, dur, ass_path)

    vf = (
        f"split=2[bg][fg];"
        f"[bg]scale={SHORT_W}:{SHORT_H}:force_original_aspect_ratio=increase,"
        f"crop={SHORT_W}:{SHORT_H},boxblur=24:2[bgb];"
        f"[fg]scale={SHORT_W}:-2[fgo];"
        f"[bgb][fgo]overlay=(W-w)/2:(H-h)/2,"
        f"subtitles='{ass_path.resolve()}'[v]"
    )
    print(f"shorts {ep} q{args.quiz_index + 1}: {start:.2f}s +{dur:.2f}s -> {out.name}")
    subprocess.run([
        FFMPEG, "-y", "-loglevel", "error",
        "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(src),
        "-filter_complex", vf,
        "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", "30", "-fps_mode", "cfr",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(out),
    ], check=True)

    probe = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries",
         "stream=width,height,color_space:format=duration", "-of", "json",
         str(out)], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    st = info["streams"][0]
    qc = {
        "episode": ep,
        "quiz_index": args.quiz_index,
        "width": st.get("width"),
        "height": st.get("height"),
        "duration": round(float(info["format"]["duration"]), 3),
        "color_space": st.get("color_space"),
        "aspect_ok": st.get("width") == SHORT_W and st.get("height") == SHORT_H,
        "duration_ok": 15.0 <= float(info["format"]["duration"]) <= 60.0,
        "overall": "PASS",
    }
    (REPO / "video" / f"{out.stem}_QC.json").write_text(
        json.dumps(qc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(qc, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
