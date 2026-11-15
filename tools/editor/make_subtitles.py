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

WRAP = 16          # max chars per line (T3: 1行13-16字・最大2行)
MAX_LINES = 2      # max lines per subtitle event
FONT = "Noto Sans JP"
SIZE = 52          # lead feedback: 42 -> 52
OUTLINE = 4
SHADOW = 3
SHADOW_ALPHA = 0x46  # 70
MARGIN_V = 79       # +21 (qa-visual): subtitle bottom lands in the 90px safe area

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
_LINE_HEAD_FORBIDDEN = "ゃゅょっぁぃぅぇぉゎゎ、。！？」》）』,:;・!?"

# 行頭禁則セット (lead指摘): chunks/lines must not START with these
_LINE_HEAD_FORBIDDEN = "ゃゅょっぁぃぅぇぉゎゎ、。！？」》）』,:;・!?"

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


# 形態素マージ辞書 (lead指摘 ~10語 + qa-visual 実例 + シリーズ主要語):
# 連結面がこれらに一致する隣接トークン列は 1 ブロック扱い (分割禁止)
_COMPOUNDS = {
    "少納言", "持ち帰る", "持ち帰った", "数十軒", "縄文時代", "弥生時代",
    "古墳時代", "奈良時代", "平安時代", "鎌倉時代", "室町時代", "江戸時代",
    "鎌倉幕府", "室町幕府", "江戸幕府", "十七条憲法", "大宝律令", "御成敗式目",
    "蒙古襲来絵詞", "平城上皇", "藤原薬子", "日出づる処", "大日本帝国憲法",
    "日本国憲法", "源頼朝", "足利尊氏", "織田信長", "豊臣秀吉", "徳川家康",
    "ペリー来航", "黒船来航", "大政奉還", "王政復古", "廃藩置県",
    "文明開化", "自由民権", "日清戦争", "日露戦争", "満洲事変",
    "沖縄戦", "太平洋戦争", "第二次世界大戦", "帝国議会",
}
_NUM_UNITS = {"年", "月", "日", "代", "世紀", "頃", "万", "千", "百年",
              "天皇", "期"}


def _is_numlike(t: dict) -> bool:
    return (any(ch.isdigit() for ch in t["s"]) or t["p2"] == "数詞"
            or t["s"] in _NUM_UNITS or t["s"] in ("紀元前", "西暦"))


_subtitle_dict_cache: set[str] | None = None
_subtitle_patterns_cache: list[re.Pattern] | None = None


def _load_subtitle_dict() -> set[str]:
    """content/subtitle_dictionary.txt (writer 管理) の不可分割語を返す。
    ファイルが無い/空の場合は空集合 (writer 追加待ち)。"""
    return _load_subtitle_dict_all()[0]


def _load_subtitle_dict_patterns() -> list[re.Pattern]:
    """@pattern 行のコンパイル済み正規表現を返す (@pattern <正規表現>)。"""
    return _load_subtitle_dict_all()[1]


def _load_subtitle_dict_all() -> tuple[set[str], list[re.Pattern]]:
    global _subtitle_dict_cache, _subtitle_patterns_cache
    if _subtitle_dict_cache is None or _subtitle_patterns_cache is None:
        words: set[str] = set()
        pats: list[re.Pattern] = []
        for cand in ("content/subtitle_dictionary.txt",):
            try:
                with open(cand, encoding="utf-8") as f:
                    for line in f:
                        w = line.strip()
                        if not w or w.startswith("#"):
                            continue
                        if w.startswith("@pattern"):
                            pat = w[len("@pattern"):].strip()
                            if pat:
                                try:
                                    pats.append(re.compile(pat))
                                except re.error:
                                    print(f"[subtitles][warn] bad @pattern: {pat!r}")
                            continue
                        words.add(w)
            except FileNotFoundError:
                pass
        _subtitle_dict_cache = words
        _subtitle_patterns_cache = pats
    return _subtitle_dict_cache, _subtitle_patterns_cache


def _merge_tokens(toks: list[dict]) -> list[dict]:
    """Apply merge passes so compound/numeric/auxiliary runs behave as one
    token (分割禁止ブロック化 — lead指摘 ~10語の辞書追記相当):

    1. adjacent 助動詞 runs (でし+ょう -> でしょう)
    2. numeric runs: digit/数詞 tokens + trailing units (70+1年 -> 701年,
       約+1万年前 -> 約1万年前)
    3. compound concatenations in _COMPOUNDS (少+納言 -> 少納言,
       持ち+帰る -> 持ち帰る)
    """
    toks = [dict(t) for t in toks]

    # 1) adjacent 助動詞 runs
    out: list[dict] = []
    i = 0
    while i < len(toks):
        if toks[i]["p1"] == "助動詞":
            j = i
            while j + 1 < len(toks) and toks[j + 1]["p1"] == "助動詞":
                j += 1
            out.append({"s": "".join(t["s"] for t in toks[i:j + 1]),
                        "p1": toks[i]["p1"], "p2": toks[i]["p2"],
                        "start": toks[i]["start"]})
            i = j + 1
        else:
            out.append(toks[i])
            i += 1
    toks = out

    # 2) numeric runs: [short 名詞 prefix] + digits + units — one block
    #    (日清戦争+1894+年 -> 日清戦争1894年, 慶応+3年 -> 慶応3年)
    out = []
    i = 0
    while i < len(toks):
        has_prefix = (out and out[-1]["p1"] == "名詞"
                      and len(out[-1]["s"]) <= 4 and not _is_numlike(out[-1]))
        if _is_numlike(toks[i]):
            j = i
            while (j + 1 < len(toks)
                   and (_is_numlike(toks[j + 1])
                        or toks[j + 1]["s"] in _NUM_UNITS)):
                j += 1
            run = "".join(t["s"] for t in toks[i:j + 1])
            if has_prefix:
                out[-1]["s"] += run  # prefix + numeric run: single block
            else:
                out.append({"s": run, "p1": toks[i]["p1"],
                            "p2": toks[i]["p2"], "start": toks[i]["start"]})
            i = j + 1
            continue
        out.append(toks[i])
        i += 1
    toks = out

    # 2.5) @pattern 正規表現による統合 (辞書の @pattern 行; writer 追加可能)
    _pats = _load_subtitle_dict_patterns()
    if _pats:
        full = "".join(t["s"] for t in toks)
        bounds = []
        acc = 0
        for t in toks:
            bounds.append((acc, acc + len(t["s"])))
            acc += len(t["s"])
        spans = []
        for pat in _pats:
            for mm in pat.finditer(full):
                spans.append((mm.start(), mm.end()))
        if spans:
            spans.sort()
            groups: list[list[int]] = []
            for gs, ge in spans:
                if groups and gs <= groups[-1][1]:
                    groups[-1][1] = max(groups[-1][1], ge)
                else:
                    groups.append([gs, ge])
            covered = set()
            for gs, ge in groups:
                covered.update(range(gs, ge))
            out = []
            i = 0
            while i < len(toks):
                if bounds[i][0] in covered:
                    j = i
                    while j + 1 < len(toks) and bounds[j + 1][0] in covered:
                        j += 1
                    out.append({"s": "".join(t["s"] for t in toks[i:j + 1]),
                                "p1": toks[i]["p1"], "p2": toks[i]["p2"],
                                "start": toks[i]["start"]})
                    i = j + 1
                else:
                    out.append(toks[i])
                    i += 1
            toks = out

    # 3) compound concatenations
    out = []
    i = 0
    while i < len(toks):
        merged = False
        for ln in (5, 4, 3, 2):
            if i + ln <= len(toks):
                cand = "".join(t["s"] for t in toks[i:i + ln])
                if cand in _COMPOUNDS or cand in _load_subtitle_dict():
                    out.append({"s": cand, "p1": toks[i]["p1"],
                                "p2": toks[i]["p2"],
                                "start": toks[i]["start"]})
                    i += ln
                    merged = True
                    break
        if not merged:
            out.append(toks[i])
            i += 1
    return out


def bunsetsu_starts(text: str) -> list[tuple[int, bool, bool]]:
    """(offset, strong, proper_junction) where a CONTENT word starts.

    Marking rule (qa-visual P2 fix): only content classes (名詞/動詞/形容詞/
    副詞/連体詞/感動詞/接頭辞) start a bunsetsu — 助詞/助動詞/接尾/記号 attach
    backward and NEVER mark a boundary, so conjugation pieces (でし|ょう,
    退けられ|ます) and compounds with suffixes (数十|軒) stay whole.
    Tokens are pre-merged via _merge_tokens (lead指摘の辞書追記相当).
    proper_junction=True flags noun junctions touching a 固有名詞 (worst cut
    points, last resort)."""
    tk = _get_tokenizer()
    if not tk:
        return []
    try:
        toks: list[dict] = []
        pos = 0
        for m in tk.tokenize(text):
            pi = m.part_of_speech()
            pos1, pos2 = (pi[0], pi[1]) if isinstance(pi, (list, tuple)) \
                else (str(pi), "")
            toks.append({"s": m.surface().strip(), "raw": m.surface(),
                         "p1": pos1, "p2": pos2, "start": pos})
            pos += len(m.surface())
        toks = _merge_tokens(toks)
        marks: list[tuple[int, bool, bool]] = []
        prev_pos = ("", "")
        for t in toks:
            pos1 = t["p1"]
            content = pos1 in ("名詞", "動詞", "形容詞", "副詞", "連体詞",
                               "感動詞", "接頭辞") or pos1 == "名詞"
            if content:
                proper = ("固有" in t["p2"] or "固有" in prev_pos[1]) \
                    and prev_pos[0] == "名詞" and pos1 == "名詞"
                marks.append((t["start"], True, proper))
                prev_pos = (pos1, pos2)
        return marks
    except Exception as exc:  # pragma: no cover
        print(f"[subtitles] bunsetsu analysis failed ({exc}); char fallback")
        return []


def _best_cut(text: str, limit: int, starts: list[tuple[int, bool, bool]],
              min_keep: int = 6, max_line: int = 18) -> int:
    """Best split offset for text (lead 2026-11-15 final spec).

    Boundary search window extends to max_line (18字延長許容) so compound
    words never split mid-token: prefer in-budget boundaries (strong >
    weak-non-proper), then the NEAREST over-budget boundary, then
    punctuation, then the hard cut."""
    limit = min(limit, len(text))
    max_line = min(max_line, len(text))
    strong_in, weak_in = [], []
    strong_over, weak_over, proper = [], [], []
    for o, s, pj in starts:
        if not (min_keep <= o <= max_line):
            continue
        if s:
            (strong_in if o <= limit else strong_over).append(o)
        elif pj:
            (proper if o > limit else proper).append(o)
        else:
            (weak_in if o <= limit else weak_over).append(o)
    for tier in (strong_in, weak_in):
        if tier:
            return max(tier)
    for tier in (strong_over, weak_over):
        if tier:
            return min(tier)
    if proper:
        return max(proper)
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
            if j != -1 and len(c) - j <= WRAP:
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
            sub_starts = [(o - pos, s, pj) for o, s, pj in starts
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


_OPENER_TO_CLOSER = {"「": "」", "（": "）", "《": "》", "『": "』"}


def _matching_closer(text: str, j: int) -> int:
    """Position AFTER the closer matching the opener at text[j] (-1 if none)."""
    op = text[j]
    cl = _OPENER_TO_CLOSER.get(op)
    if not cl:
        return -1
    depth = 0
    for k in range(j, len(text)):
        ch = text[k]
        if ch == op:
            depth += 1
        elif ch == cl:
            depth -= 1
            if depth == 0:
                return k + 1
    return -1


def _wrap_2lines(text: str, first_budget: int,
                 starts: list[tuple[int, bool, bool]] | None = None) -> str:
    """Wrap a chunk to <=2 lines (T3: 1行13-16字・最大2行).

    Chunks <= WRAP stay on one line. Longer chunks split at the bunsetsu
    boundary nearest the midpoint (balanced), never mid-compound; a cut that
    lands inside an unmatched 「…」 relocates past the closer (or just before
    the opener for long quotes)."""
    if len(text) <= WRAP:
        return text
    starts = sorted(starts or [])
    # balanced midpoint, nudged down for the speaker label on line 1
    target = max((len(text) + 1) // 2 - (first_budget - 8), 6)
    limit = min(max(target, 8), len(text) - 6)
    cut = _best_cut(text, limit, starts, min_keep=6)
    # bracket integrity: a cut inside an unmatched opener relocates
    j = _unmatched_opener_pos(text[:cut])
    if j != -1:
        closer = _matching_closer(text, j)
        if closer != -1 and closer <= WRAP + 10:
            cut = closer
        else:
            cut = j
    line1, line2 = text[:cut], text[cut:]
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
    banner_active_until = 0.0  # banner 表示ウィンドウの終端 (表示開始+3.2s)
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
            # P2: exam_banner 表示中の字幕開始を 0.3s 遅延 (重複対策)。
            # banner は ~3.2s 表示が続くため、後続ビートの字幕も遅延する
            has_banner = any(
                o.get("style") in ("exam_banner", "subscribe_banner")
                for o in (sb.get("overlay_text") or []))
            if has_banner:
                banner_active_until = end + 3.2
            if start < banner_active_until:
                start = start + 0.3
            # P1 fix: 前イベントがこのビートのウィンドウを食んでいる場合は
            # 前イベントの end を短縮してビート開始を確保 (タイミング崩壊防止)
            if events and events[-1]["end"] > start - 0.05:
                events[-1]["end"] = max(events[-1]["start"] + 0.3, start - 0.05)
                prev_end = events[-1]["end"]
            start = max(start, prev_end)  # never overlap
            # P1 fix: 最小表示 0.8s (ゼロ秒字幕の防止)
            if end - start < 0.8:
                end = start + 0.8
            events.append({
                "scene": sid,
                "start": start,
                "end": end,
                "speaker": speaker,
                "label": (ch.get("name") if ch else "") or "",
                "color": (ch.get("subtitle_color") if ch else "") or "",
                "text": sb.get("text", ""),
                "margin_v": 250 if sc.get("section") == "points" else MARGIN_V,
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
    first_budget = max(WRAP - len(prefix), 6)  # label eats line-1 budget
    capacity = first_budget + WRAP  # 2 lines per event
    text = _sanitize(ev["text"])
    starts = bunsetsu_starts(text)
    chunks = _fix_chunk_boundaries(
        _split_sentences(text, capacity, starts)) or [""]
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
            mv = ev.get("margin_v", MARGIN_V)
            lines.append(f"Dialogue: 0,{ass_time(st)},{ass_time(en)},"
                         f"Sub,,0,0,{mv},,{txt}\n")
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
