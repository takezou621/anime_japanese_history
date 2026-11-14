# -*- coding: utf-8 -*-
"""ASS subtitle generator (editor pipeline).

Builds burned-in dialogue subtitles from timing.json (global beat times) +
script.json (text / speakers / colors). The resulting .ass is burned by
assemble.py on the FINAL timeline via the libass ``subtitles`` filter, so
global times can be used 1:1 — the assembly plan keeps the final video
timeline identical to timing.json (section xfades borrow head/tail pads, see
tools/editor/README.md).

Rules (docs/03_STYLE_GUIDE.md §3 字幕ルール + lead feedback on the 10s test):
- 52px NotoSansJP Bold, black 4px outline + shadow (y+3, alpha 70)
- rounded translucent black band behind the subtitle zone (drawn by
  assemble.py as an overlay PNG; see tools/editor/text_overlays.py)
- speaker label ("ヒスト先生:") colored + bold; body white for readability
- manual wrapping: max 22 full-width chars per line, max 2 lines;
  longer narration is split into sequential sub-events (durations
  proportional to character count)

timing.json contract (tools/audio, as delivered for ep01):
    {"episode": "ep01", "total_duration": 575.561,
     "scenes": [{"id": "s01", "section": "opening", "start": 0.0,
                 "beats": [{"speaker": "sensei", "wav": "narration/s01_b00.wav",
                            "start": 0.0, "duration": 5.909, "text": "..."}]}]}
- scene duration may be omitted -> derived from the next scene's start
  (last scene: total_duration). beats[].start is GLOBAL seconds.
- beat end = start + duration when present, else next beat start.
"""
from __future__ import annotations

import argparse
import json
import re

WRAP = 22          # max chars per line (full-width)
MAX_LINES = 2      # max lines per subtitle event
FONT = "Noto Sans JP"
SIZE = 52          # lead feedback: 42 -> 52
OUTLINE = 4
SHADOW = 3
SHADOW_ALPHA = 0x46  # 70
MARGIN_V = 58       # keeps 52px text centered inside the bottom band

_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H{shadow_alpha:02X}000000,1,0,0,0,100,100,0,0,1,{outline},{shadow},2,60,60,{marginv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

_SENT_END = "。！？…!?"


def ass_time(sec: float) -> str:
    sec = max(sec, 0.0)
    cs = int(round(sec * 100))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, cc = divmod(rem, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cc:02d}"


def ass_color(hexcolor: str | None) -> str:
    """'#7ec8e3' -> '&HE3C87E&' (ASS uses &HBBGGRR&)."""
    if not hexcolor:
        return "&HFFFFFF&"
    h = hexcolor.lstrip("#")
    if len(h) != 6:
        return "&HFFFFFF&"
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{b}{g}{r}&".upper().replace("X", "x")


def _split_sentences(text: str, capacity: int) -> list[str]:
    """Split text into chunks of <= capacity chars, preferring sentence ends."""
    text = re.sub(r"\s+", " ", str(text)).strip()
    if not text:
        return []
    chunks: list[str] = []
    buf = ""
    for ch in text:
        buf += ch
        if len(buf) >= capacity or (ch in _SENT_END and len(buf) >= capacity * 0.4):
            chunks.append(buf)
            buf = ""
    if buf:
        if chunks and len(buf) <= 4:
            chunks[-1] += buf
        else:
            chunks.append(buf)
    # hard-split any remaining oversized chunk
    out: list[str] = []
    for c in chunks:
        while len(c) > capacity:
            out.append(c[:capacity])
            c = c[capacity:]
        if c:
            out.append(c)
    return out


def _fix_line_starts(lines: list[str]) -> list[str]:
    """禁則処理: avoid lines starting with closing punctuation."""
    closes = "、。！？…!?）」』,:;・-"
    out = list(lines)
    for i in range(1, len(out)):
        moved = ""
        while out[i] and out[i][0] in closes and len(out[i - 1]) < WRAP + 2:
            moved += out[i][0]
            out[i] = out[i][1:]
        if moved:
            out[i - 1] += moved
    return out


_BREAK_AFTER = "、。！？…!?）」』,:;・"


def _wrap_2lines(text: str, first_budget: int) -> str:
    """Wrap a chunk to <=2 lines with \\N (lead: 22 chars/line manual wrap).

    Line 1 budget is smaller when a speaker label is prefixed. Prefer breaking
    after sentence punctuation: first try near the budget edge, then fall back
    to the nearest earlier punctuation as long as line 2 stays <= WRAP+4.
    """
    if len(text) <= first_budget:
        return text
    buf, rest = text[:first_budget], text[first_budget:]

    def line2_len(cut: int) -> int:
        return (len(buf) - cut) + len(rest)

    cut = 0  # 0 == hard cut at the budget edge
    for j in range(len(buf) - 1, -1, -1):
        if buf[j] in _BREAK_AFTER:
            if line2_len(j + 1) <= WRAP + 4:
                cut = j + 1
            break  # nearest punctuation wins; if it overflows, hard cut
    line1 = buf[:cut] if cut else buf
    line2 = (buf[cut:] + rest) if cut else rest
    lines = [ln for ln in (line1, line2) if ln]
    lines = _fix_line_starts(lines)
    lines = [ln for ln in lines if ln]
    return "\\N".join(lines)


def scene_windows(timing: dict) -> tuple[dict, float]:
    """Normalize timing.json -> {scene_id: (start, end)}, plus total.

    Scene duration may be omitted in the audio contract; derive it from the
    next scene's start (last scene: total_duration, or its last beat's end).
    """
    scenes = sorted(timing.get("scenes", []), key=lambda s: float(s["start"]))
    total = float(timing.get("total_duration") or timing.get("total") or 0.0)
    windows: dict[str, tuple[float, float]] = {}
    for i, s in enumerate(scenes):
        start = float(s["start"])
        if s.get("duration") is not None:
            end = start + float(s["duration"])
        elif i + 1 < len(scenes):
            end = float(scenes[i + 1]["start"])
        else:
            beats = s.get("beats") or []
            if beats and total <= start:
                last = beats[-1]
                end = float(last.get("start", start)) + \
                    float(last.get("duration", 0.0))
            else:
                end = total if total > start else start
        windows[s.get("id")] = (start, end)
        if total < end:
            total = end
    return windows, total


def build_events(script: dict, timing: dict) -> list[dict]:
    """Join script beats with timing beat times -> ordered event dicts."""
    chars = {c.get("id"): c for c in script.get("characters", [])}
    windows, _total = scene_windows(timing)
    events: list[dict] = []
    prev_end = 0.0
    for sc in script.get("scenes", []):
        sid = sc.get("id")
        if sid not in windows:
            raise KeyError(
                f"timing.json has no entry for scene {sid!r}; "
                "audio/timing must cover every script scene")
        s_start, s_end = windows[sid]
        tbeats = (timing_scenes(timing).get(sid) or {}).get("beats") or []
        sbeats = sc.get("beats", [])
        if tbeats and len(tbeats) != len(sbeats):
            print(f"[subtitles][warn] scene {sid}: script beats={len(sbeats)} "
                  f"vs timing beats={len(tbeats)}; aligning by index")
        for i, sb in enumerate(sbeats):
            tb = tbeats[i] if i < len(tbeats) else {}
            start = float(tb.get("start", s_start))
            if tb.get("duration") is not None:
                end = start + float(tb["duration"])
            elif i + 1 < len(tbeats):
                end = float(tbeats[i + 1]["start"])
            else:
                end = s_end
            end = min(end, s_end)
            if end - start < 0.05:
                end = start + 0.05
            speaker = tb.get("speaker") or sb.get("speaker") or ""
            ch = chars.get(speaker)
            events.append({
                "scene": sid,
                "start": max(start, prev_end),  # never overlap
                "end": end,
                "speaker": speaker,
                "label": (ch.get("name") if ch else "") or "",
                "color": (ch.get("subtitle_color") if ch else "") or "",
                "text": sb.get("text", ""),
            })
            prev_end = events[-1]["end"]
    return events


def timing_scenes(timing: dict) -> dict:
    return {s.get("id"): s for s in timing.get("scenes", [])}


def _sanitize(text: str) -> str:
    """Strip characters that would break ASS override tags."""
    return (str(text).replace("{", "（").replace("}", "）")
            .replace("\n", " ").strip())


def event_to_dialogues(ev: dict) -> list[tuple[float, float, str]]:
    """One event -> list of (start, end, ass_text) sub-events (max 2 lines each)."""
    label = _sanitize(ev.get("label") or "")
    prefix = f"{label}: " if label else ""
    first_budget = max(WRAP - len(prefix), 8)
    capacity = first_budget + WRAP  # 2 lines per event
    chunks = _split_sentences(_sanitize(ev["text"]), capacity) or [""]
    dur = max(ev["end"] - ev["start"], 0.05)
    weights = [max(len(c), 1) for c in chunks]
    total_w = sum(weights)
    out: list[tuple[float, float, str]] = []
    t = ev["start"]
    color = ass_color(ev.get("color"))
    for i, c in enumerate(chunks):
        d = dur * weights[i] / total_w
        e = ev["end"] if i == len(chunks) - 1 else t + d
        body = _wrap_2lines(c, first_budget)
        if prefix:
            # colored + bold speaker label, white body (lead feedback)
            txt = (f"{{\\1c{color}\\b1}}{prefix[:-1]}{{\\b0\\1c&HFFFFFF&}} "
                   f"{body}")
        else:
            txt = f"{{\\1c{color}}}{body}"
        out.append((t, e, txt))
        t = e
    return out


def render_ass(events: list[dict]) -> str:
    lines = [_HEADER.format(font=FONT, size=SIZE, outline=OUTLINE,
                            shadow=SHADOW, shadow_alpha=SHADOW_ALPHA,
                            marginv=MARGIN_V)]
    for ev in events:
        for st, en, txt in event_to_dialogues(ev):
            lines.append(f"Dialogue: 0,{ass_time(st)},{ass_time(en)},"
                         f"Sub,,0,0,0,,{txt}\n")
    return "".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="timing.json + script.json -> ASS")
    ap.add_argument("--script", required=True)
    ap.add_argument("--timing", required=True)
    ap.add_argument("--out", required=True, help="output .ass path")
    a = ap.parse_args()
    with open(a.script, encoding="utf-8") as f:
        script = json.load(f)
    with open(a.timing, encoding="utf-8") as f:
        timing = json.load(f)
    events = build_events(script, timing)
    ass = render_ass(events)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(ass)
    print(f"subtitles: {len(events)} beat events -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
