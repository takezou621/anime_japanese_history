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
_OPENERS = "「（《『"
_CLOSERS = "」》）』"
# 行頭禁則セット (lead指摘): chunks/lines must not START with these
_LINE_HEAD_FORBIDDEN = "」》）』、。！？…,:;・!?"

# 行頭禁則セット (lead指摘): chunks/lines must not START with these
_LINE_HEAD_FORBIDDEN = "」》）』、。！？…,:;・!?"

# ---------------------------------------------------------------------------
# bunsetsu (文節) boundaries — P2-1 fix (qa_visual ep01-03: 単語途中分割)
# sudachipy があれば形態素ベースの境界を使い、無ければ従来の文字ベースに
# フォールバックする (uv run --with sudachipy --with sudachidict-core 推奨)
# ---------------------------------------------------------------------------

_tokenizer = None
_tokenizer_checked = False


def _get_tokenizer():
    global _tokenizer, _tokenizer_checked
    if not _tokenizer_checked:
        _tokenizer_checked = True
        try:
            from sudachipy import Dictionary
            dic = Dictionary()
            _tokenizer = (dic.tokenizer() if hasattr(dic, "tokenizer")
                          else dic.create())
        except Exception as exc:  # pragma: no cover - optional dependency
            print(f"[subtitles] sudachipy unavailable ({exc}); "
                  "falling back to character-based splitting")
            _tokenizer = False
    return _tokenizer


def bunsetsu_starts(text: str) -> list[tuple[int, bool]]:
    """(offset, strong) where a bunsetsu starts. strong=False marks junctions
    that are morpheme boundaries but bad cut points (noun-noun compounds like
    縄文|時代, or before suffixes like 645|年)."""
    tk = _get_tokenizer()
    if not tk:
        return []
    try:
        marks: list[tuple[int, bool, str, str]] = []
        pos = 0
        prev_pos1 = ""
        for m in tk.tokenize(text):
            pos_info = m.part_of_speech()
            pos1 = pos_info[0] if isinstance(pos_info, (list, tuple)) \
                else str(pos_info)
            if pos1 not in ("助詞", "助動詞") and not pos1.startswith("補助記号"):
                strong = not (pos1 in ("接尾", "数詞") or
                              prev_pos1 in ("接頭辞", "数詞") or
                              (prev_pos1 == "名詞" and pos1 == "名詞"))
                marks.append((pos, strong, pos1, prev_pos1))
                prev_pos1 = pos1
            pos += len(m.surface())
        # (offset, strong) only — keep the API small
        return [(o, s) for o, s, _p1, _pp in marks]
    except Exception as exc:  # pragma: no cover
        print(f"[subtitles] bunsetsu analysis failed ({exc}); char fallback")
        return []


def _best_cut(text: str, limit: int, starts: list[tuple[int, bool]],
              min_keep: int = 6) -> int:
    """Best split offset <= limit for text. Preference: strong bunsetsu
    boundary > weak boundary > punctuation > hard cut. Returns an offset in
    [min_keep, len(text)]."""
    limit = min(limit, len(text))
    strong = [o for o, s in starts if s and min_keep <= o <= limit]
    if strong:
        return max(strong)
    weak = [o for o, s in starts if not s and min_keep <= o <= limit]
    if weak:
        return max(weak)
    for j in range(limit, min_keep - 1, -1):
        if text[j - 1] in _SENT_END + "、」』）":
            return j
    return limit


def _unmatched_opener_pos(c: str) -> int:
    """Index of the last opener with no matching closer in c (-1 if none)."""
    stack: list[int] = []
    for j, ch in enumerate(c):
        if ch in _OPENERS:
            stack.append(j)
        elif ch in _CLOSERS and stack:
            stack.pop()
    return stack[-1] if stack else -1


def _fix_chunk_boundaries(chunks: list[str]) -> list[str]:
    """禁則処理 across sub-event chunks.

    - a chunk never starts with a closing mark / sentence punctuation
      (pull it back into the previous chunk)
    - a chunk never ends with an opening bracket (push it forward)
    - a chunk never ends INSIDE a 「…」 bracket: the whole unmatched opener
      tail moves to the next chunk so bracketed terms stay intact
    May exceed capacity by 1-2 chars for typographic correctness.
    """
    for i in range(len(chunks) - 1):
        c, nxt = chunks[i], chunks[i + 1]
        for _ in range(4):  # converge the interacting rules
            changed = False
            while c and c[-1] in _OPENERS:
                nxt = c[-1] + nxt
                c = c[:-1]
                changed = True
            while nxt and nxt[0] in _LINE_HEAD_FORBIDDEN:
                c += nxt[0]
                nxt = nxt[1:]
                changed = True
            j = _unmatched_opener_pos(c)
            if j != -1:
                nxt = c[j:] + nxt
                c = c[:j]
                changed = True
            if not changed:
                break
        chunks[i], chunks[i + 1] = c, nxt
    return [c for c in chunks if c]


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


def _split_sentences(text: str, capacity: int,
                     starts: list[tuple[int, bool]] | None = None) -> list[str]:
    """Split text into chunks of <= capacity chars.

    Preference: sentence ends (。) > strong bunsetsu boundaries (sudachi) >
    weak boundaries > hard cut.
    `starts` holds bunsetsu boundary (offset, strong) tuples into `text`.
    """
    text = re.sub(r"\s+", " ", str(text)).strip()
    if not text:
        return []
    starts = sorted(starts or [])
    chunks: list[str] = []
    pos = 0
    while pos < len(text):
        room = min(capacity, len(text) - pos)
        piece = text[pos:pos + room]
        # sentence end inside the piece (>=40% full) -> cut right after it
        sent_cut = 0
        for j, ch in enumerate(piece):
            if ch in _SENT_END:
                sent_cut = j + 1
        # piece fills capacity and no sentence end -> bunsetsu cut
        if room >= capacity and sent_cut < int(capacity * 0.4):
            sub_starts = [(o - pos, s) for o, s in starts
                          if pos < o <= pos + room]
            sent_cut = _best_cut(piece, capacity, sub_starts)
        if sent_cut <= 0:
            sent_cut = room
        chunks.append(text[pos:pos + sent_cut])
        pos += sent_cut
    # merge tiny remainders (e.g. lone 。)
    out: list[str] = []
    for c in chunks:
        c = c.strip() or c
        if c and len(c) <= 4 and out and not out[-1].endswith("」"):
            out[-1] += c
        elif c:
            out.append(c)
    return [c for c in out if c]


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


def _wrap_2lines(text: str, first_budget: int,
                 starts: list[int] | None = None) -> str:
    """Wrap a chunk to <=2 lines with \\N (lead: 22 chars/line manual wrap).

    Line 1 budget is smaller when a speaker label is prefixed. Split point
    preference: bunsetsu boundary (sudachi) > sentence punctuation > hard cut
    (qa_visual P2-1: 単語途中分割の解消).
    """
    if len(text) <= first_budget:
        return text
    starts = sorted(starts or [])
    if starts:
        cut = _best_cut(text, first_budget, starts, min_keep=8)
    else:
        cut = 0
        for j in range(first_budget, 0, -1):
            if text[j - 1] in _BREAK_AFTER:
                cut = j
                break
    line1 = text[:cut] or text[:first_budget]
    line2 = text[len(line1):]
    # a line must not END with an opening bracket (push it to the next line)
    while line1 and line1[-1] in _OPENERS:
        line2 = line1[-1] + line2
        line1 = line1[:-1]
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
    chunks = _fix_chunk_boundaries(
        _split_sentences(_sanitize(ev["text"]), capacity)) or [""]
    dur = max(ev["end"] - ev["start"], 0.05)
    weights = [max(len(c), 1) for c in chunks]
    total_w = sum(weights)
    out: list[tuple[float, float, str]] = []
    t = ev["start"]
    color = ass_color(ev.get("color"))
    for i, c in enumerate(chunks):
        d = dur * weights[i] / total_w
        e = ev["end"] if i == len(chunks) - 1 else t + d
        body = _wrap_2lines(c, first_budget, bunsetsu_starts(c))
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
