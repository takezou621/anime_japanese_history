#!/usr/bin/env python3
"""Synthesize the project's standard SFX set (no external samples).

Writes 48kHz mono 16-bit WAVs into assets/audio/sfx/:
  se_correct.wav  quiz correct-answer two-tone chime (E6 -> A6)
  se_question.wav quiz board appearance, soft single chime (C6+G6)
  se_point.wav    exam-point banner sparkle (C7 -> E7, very short)
  se_section.wav  section transition, soft filtered-noise whoosh
"""
import math, struct, wave
from pathlib import Path

SR = 48000
OUT = Path("assets/audio/sfx")
OUT.mkdir(parents=True, exist_ok=True)


def save(name, samples):
    p = OUT / name
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(
            struct.pack("<h", max(-32767, min(32767, int(s * 32767))))
            for s in samples))
    print(p, f"{len(samples) / SR:.2f}s")


def tone(freq, dur, amp, tau, delay=0.0, total=0.0):
    n = int(total * SR)
    out = [0.0] * n
    start = int(delay * SR)
    for i in range(int(dur * SR)):
        t = i / SR
        env = math.exp(-t / tau) * min(1.0, t / 0.004)
        v = amp * env * math.sin(2 * math.pi * freq * t)
        if start + i < n:
            out[start + i] += v
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] if i < len(t) else 0.0 for t in tracks)
            for i in range(n)]


# correct: pin-pon (E6 then A6), total 0.55s
save("se_correct.wav", mix(
    tone(1318.51, 0.13, 0.42, 0.055, total=0.55),
    tone(1760.00, 0.42, 0.42, 0.14, delay=0.11, total=0.55)))
# question: soft C6 with G6 shimmer, 0.30s
save("se_question.wav", mix(
    tone(1046.50, 0.30, 0.34, 0.085, total=0.30),
    tone(1567.98, 0.30, 0.13, 0.07, total=0.30)))
# point: tiny sparkle C7 -> E7, 0.20s
save("se_point.wav", mix(
    tone(2093.00, 0.07, 0.30, 0.028, total=0.20),
    tone(2637.02, 0.13, 0.26, 0.05, delay=0.05, total=0.20)))
# section: filtered noise whoosh 0.40s (one-pole LP, swept)
import random
random.seed(42)
n = int(0.40 * SR)
buf = []
lp = 0.0
for i in range(n):
    t = i / SR
    alpha = 0.02 + 0.30 * math.sin(math.pi * min(1.0, t / 0.40)) ** 2
    lp += alpha * (random.uniform(-1, 1) - lp)
    env = math.sin(math.pi * min(1.0, t / 0.40)) ** 1.5
    buf.append(0.5 * env * lp)
save("se_section.wav", buf)
