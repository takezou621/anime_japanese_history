"""Voice consistency gate (voice consistency system).

For each character, measures every beat WAV in audio/<ep>/narration_unified/:
  - median fundamental frequency (F0) via autocorrelation
  - speaking rate (spoken chars / second, from the script text)
and flags beats that deviate strongly from the character median:
  - F0 deviation > 15%
  - rate deviation > 25%
Exit code 1 if any beat is flagged (gate). Flagged beats must be
regenerated (delete the WAV and rerun gen_narration_unified.py).

Usage (repo root):
  uv run --with numpy python tools/audio/check_voice_consistency.py --episode ep01
"""
import argparse, json, math, wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).parent.parent.parent


def read_wav(path: Path):
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    return x, sr


def median_f0(x: np.ndarray, sr: int) -> float:
    frame = int(sr * 0.04)
    hop = int(sr * 0.02)
    f0s = []
    lo = int(sr / 400)   # 400 Hz
    hi = int(sr / 60)    # 60 Hz
    for start in range(0, max(1, len(x) - frame), hop):
        seg = x[start:start + frame]
        if len(seg) < frame or np.sqrt(np.mean(seg ** 2)) < 0.02:
            continue
        seg = seg - seg.mean()
        ac = np.correlate(seg, seg, mode="full")[len(seg) - 1:]
        if ac[0] <= 0:
            continue
        window = ac[lo:hi]
        if len(window) == 0:
            continue
        peak = int(np.argmax(window)) + lo
        if ac[peak] / ac[0] > 0.35:
            f0s.append(sr / peak)
    return float(np.median(f0s)) if f0s else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True)
    args = ap.parse_args()
    ep = args.episode

    script = json.loads((REPO / "content/episodes" / ep / "script.json").read_text())
    beats = {}
    for scene in script["scenes"]:
        for bi, beat in enumerate(scene["beats"]):
            beats[f"{scene['id']}_b{bi:02d}.wav"] = beat

    ndir = REPO / "audio" / ep / "narration_unified"
    rows = []
    for wav_path in sorted(ndir.glob("*.wav")):
        beat = beats.get(wav_path.name)
        if beat is None:
            continue
        x, sr = read_wav(wav_path)
        dur = len(x) / sr
        f0 = median_f0(x, sr)
        chars = len(beat["text"].replace(" ", "").replace("　", ""))
        rate = chars / dur if dur > 0 else 0.0
        rows.append({"file": wav_path.name, "speaker": beat["speaker"],
                     "f0": round(f0, 1), "rate": round(rate, 2), "dur": round(dur, 2)})

    flagged = []
    for spk in sorted({r["speaker"] for r in rows}):
        sub = [r for r in rows if r["speaker"] == spk and r["f0"] > 0]
        if not sub:
            continue
        med_f0 = float(np.median([r["f0"] for r in sub]))
        med_rate = float(np.median([r["rate"] for r in sub]))
        for r in sub:
            reasons = []
            if abs(r["f0"] - med_f0) / med_f0 > 0.15:
                reasons.append(f"F0 {r['f0']} vs median {med_f0:.1f}")
            if med_rate > 0 and abs(r["rate"] - med_rate) / med_rate > 0.25:
                reasons.append(f"rate {r['rate']} vs median {med_rate:.2f}")
            r["flag"] = "; ".join(reasons)
            if reasons:
                flagged.append(r)
        print(f"{spk}: beats={len(sub)} median F0={med_f0:.1f} Hz median rate={med_rate:.2f} chars/s")

    report = {"episode": ep, "rows": rows, "flagged": flagged}
    out = REPO / "audio" / ep / "voice_consistency_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1))
    if flagged:
        print(f"GATE FAIL: {len(flagged)} beat(s) flagged:")
        for r in flagged:
            print(f"  {r['file']} [{r['speaker']}] {r['flag']}")
        return 1
    print(f"GATE PASS: {len(rows)} beats consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
