# -*- coding: utf-8 -*-
"""Layer overlap gate (added 2026-11-16, QC strengthening).

Builds the render plan for an episode and samples every character
layer's enable expression. Two layers of the SAME character with
DIFFERENT images and DIFFERENT transforms (filters/x/y) must never be
visible at the same time for longer than a crossfade margin: that is
exactly the "character appears twice" defect reported on ep01
(2026-11-16) — expression variants used a static rest transform while
the base layer slides in / pulses / bobs, so the two diverged.

Derived layers (expression variants, talk, blink) must clone their
parent layer's transform verbatim; this gate fails the sign-off if
any divergent pair overlaps beyond --max-overlap seconds.

Usage: uv run --with pillow --with sudachipy --with sudachidict-core \
    python tools/qa/layer_overlap_check.py --episode ep01
Exit code 0 = PASS, 1 = FAIL.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "editor"))
import assemble as A  # noqa: E402


def make_eval(expr: str):
    e = expr.replace("not(", "NOT(")

    def between(t, a, b):
        return 1.0 if a <= t <= b else 0.0

    def gte(t, a):
        return 1.0 if t >= a else 0.0

    def gt(t, a):
        return 1.0 if t > a else 0.0

    def lt(t, a):
        return 1.0 if t < a else 0.0

    def lte(t, a):
        return 1.0 if t <= a else 0.0

    def NOT(x):
        return 0.0 if x else 1.0

    ns = {"between": between, "gte": gte, "gt": gt, "lt": lt,
          "lte": lte, "NOT": NOT}
    code = compile(e, "<enable>", "eval")

    def f(t):
        ns["t"] = t
        try:
            return 1 if eval(code, {"__builtins__": {}}, ns) else 0
        except Exception:
            return -1

    return f


def char_group(image: str) -> str | None:
    m = re.match(r"(char_[a-z]+)", Path(image).name)
    return m.group(1) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default="ep01")
    ap.add_argument("--step", type=float, default=0.05)
    ap.add_argument("--max-overlap", type=float, default=0.35)
    a = ap.parse_args()
    ep = a.episode

    script = json.loads(
        (ROOT / "content" / "episodes" / ep / "script.json")
        .read_text(encoding="utf-8"))
    timing = json.loads(
        (ROOT / "audio" / ep / "timing.json").read_text(encoding="utf-8"))
    assets_dir = ROOT / "assets" / ep
    with tempfile.TemporaryDirectory() as td:
        text_dir = Path(td)
        spans, used = A.build_plan(script, timing, assets_dir, text_dir,
                                   None, ep=ep, ai_manifest=None)
        char_ids = [c.get("id", "") for c in script.get("characters", [])]
        quiz_list = script.get("quiz", []) or []
        quiz_ord = 0
        failures = []
        checked = 0
        for sp in spans:
            scene = next(s for s in used if s["id"] == sp.sid)
            ts = next(s for s in timing["scenes"] if s["id"] == sp.sid)
            quiz_item = None
            if sp.section == "quiz":
                if quiz_ord < len(quiz_list):
                    quiz_item = quiz_list[quiz_ord]
                quiz_ord += 1
            A.scene_layers(sp, scene, ts, assets_dir, text_dir,
                           char_ids, quiz_item)
            groups: dict = {}
            for L in sp.layers:
                g = char_group(L.image or "")
                if g:
                    groups.setdefault(g, []).append(L)
            n = int(sp.dur / a.step) + 1
            for g, layers in groups.items():
                if len(layers) < 2:
                    continue
                evs = [make_eval(L.enable) for L in layers]
                flags = [[evs[i](sp.seg_start + k * a.step)
                          for k in range(n)] for i in range(len(layers))]
                for i in range(len(layers)):
                    for j in range(i + 1, len(layers)):
                        li, lj = layers[i], layers[j]
                        if li.image == lj.image:
                            continue
                        # Geometry signature: every filter except
                        # alpha-only fades (crossfades legitimately
                        # differ), plus x/y.
                        sig_i = (tuple(f for f in li.filters
                                       if not f.startswith("fade")),
                                 li.x, li.y)
                        sig_j = (tuple(f for f in lj.filters
                                       if not f.startswith("fade")),
                                 lj.x, lj.y)
                        if sig_i == sig_j:
                            continue
                        checked += 1
                        run = best = 0
                        for k in range(n):
                            if flags[i][k] == 1 and flags[j][k] == 1:
                                run += 1
                                best = max(best, run)
                            else:
                                run = 0
                        ov = best * a.step
                        if ov > a.max_overlap:
                            failures.append(
                                f"{sp.sid} {g}: {Path(li.image).name} <> "
                                f"{Path(lj.image).name} divergent overlap "
                                f"{ov:.2f}s (global ~{sp.start:.1f}s)")
        print(f"[layer-overlap] {ep}: divergent pairs checked={checked}, "
              f"failures={len(failures)} (max allowed {a.max_overlap:.2f}s)")
        for f in failures:
            print(f"  FAIL {f}")
        print("[layer-overlap] " + ("PASS" if not failures else "FAIL"))
        return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
