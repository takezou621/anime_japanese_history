#!/usr/bin/env python3
"""Derive SFX cue times for an episode from the render plan.

Reads script.json + timing.json via the editor's plan builder and writes
audio/<ep>/sfx_cues.json: [{t, file, gain_db}] with file names relative
to assets/audio/sfx/. Cue kinds:
  quiz_board layer start  -> se_question.wav (board appears)
  quiz_answer layer start -> se_correct.wav  (answer highlight)
  exam_banner overlay     -> se_point.wav    (exam-point banner)
  section start           -> se_section.wav  (skipped when a quiz_board
                             cue lands within 1.5s, and at t=0)
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "editor"))
import assemble as A  # noqa: E402

GAINS = {"question": -19.0, "correct": -15.0, "point": -25.0,
         "section": -23.0}
FILES = {"question": "se_question.wav", "correct": "se_correct.wav",
         "point": "se_point.wav", "section": "se_section.wav"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default="ep01")
    args = ap.parse_args()
    ep = args.episode
    root = Path(".")
    script = json.loads(
        (root / f"content/episodes/{ep}/script.json").read_text())
    timing = json.loads((root / f"audio/{ep}/timing.json").read_text())
    text_dir = Path("/tmp/sfx_cue_text"); text_dir.mkdir(exist_ok=True)
    spans, used = A.build_plan(script, timing, root / f"assets/{ep}",
                               text_dir, None, ep=ep, ai_manifest=None)
    char_ids = [c.get("id", "") for c in script.get("characters", [])]
    quiz_list = script.get("quiz", []) or []
    cues = []
    qo = 0
    prev_section = None
    for sp in spans:
        scene = next(s for s in used if s["id"] == sp.sid)
        ts = next(s for s in timing["scenes"] if s["id"] == sp.sid)
        qi = None
        if sp.section == "quiz":
            if qo < len(quiz_list):
                qi = quiz_list[qo]
            qo += 1
        if sp.section != prev_section and sp.seg_start > 0.1:
            cues.append({"t": round(sp.seg_start, 2), "kind": "section",
                         "scene": sp.sid})
            prev_section = sp.section
        A.scene_layers(sp, scene, ts, root / f"assets/{ep}", text_dir,
                       char_ids, qi)
        for L in sp.layers:
            d = L.desc or ""
            m = re.match(r"quiz_board@([\d.]+)s", d)
            if m:
                cues.append({"t": round(sp.seg_start + float(m.group(1)), 2),
                             "kind": "question", "scene": sp.sid})
            m = re.match(r"quiz_answer@([\d.]+)s", d)
            if m:
                cues.append({"t": round(sp.seg_start + float(m.group(1)), 2),
                             "kind": "correct", "scene": sp.sid})
            m = re.match(r"text:exam_banner@([\d.]+)s", d)
            if m:
                cues.append({"t": round(sp.seg_start + float(m.group(1)), 2),
                             "kind": "point", "scene": sp.sid})
    qtimes = [c["t"] for c in cues if c["kind"] == "question"]
    out = []
    for c in sorted(cues, key=lambda c: c["t"]):
        if c["kind"] == "section" and any(
                abs(c["t"] - q) < 1.5 for q in qtimes):
            continue
        out.append({"t": c["t"], "file": FILES[c["kind"]],
                    "gain_db": GAINS[c["kind"]], "kind": c["kind"],
                    "scene": c["scene"]})
    dst = root / f"audio/{ep}/sfx_cues.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    for c in out:
        print(f"{c['t']:8.2f}  {c['kind']:8s} {c['scene']}  "
              f"{c['file']} {c['gain_db']:+.0f}dB")
    print(f"-> {dst} ({len(out)} cues)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
