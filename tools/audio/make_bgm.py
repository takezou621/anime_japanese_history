#!/usr/bin/env python3
"""make_bgm.py — numpy 合成 BGM (著作権完全クリア)

使い方:
    uv run --with numpy python tools/audio/make_bgm.py --episode ep01
    (make_narration.py が生成した audio/<ep>/timing.json のセクション尺を読み,
     セクション別ムードでフル尺 1 本の bgm.wav を生成する)

STYLE_GUIDE §2 のムード別コード進行:
    opening: 明るい C major 120bpm (パッド+アルペジオ)
    story:   落ち着き Am→F 90bpm (パッド中心)
    points:  軽快 F major 110bpm (スタッカート)
    quiz:    タメ Dm 100bpm (ドラム強め)
    ending:  温かい G major 85bpm

出力: 48kHz 16bit ステレオ, ループ可能 (コードは絶対時刻の bar 番号 mod 進行長 で
決まるため, どの長さで切っても位相が連続する)。ducking は行わない (mix 側でエンベロープ)。
"""
from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000

# ---------------------------------------------------------------- 音響パラメータ
MAJ = [0, 4, 7]
MIN = [0, 3, 7]

MOODS: dict[str, dict] = {
    # opening: 明るいメジャー, パッド+アルペジオ, 軽いパーカッション
    "opening": {
        "bpm": 120, "prog": [(48, MAJ), (43, MAJ), (45, MIN), (41, MAJ)],
        "pad_amp": 0.30, "bass_amp": 0.26,
        "arp": {"steps_per_bar": 8, "pattern": [0, 1, 2, 3], "amp": 0.20,
                "tau": 0.16, "staccato": 0.85, "bright": 1.0},
        "drums": {"kick": [0, 8], "snare": [], "hat": [2, 6, 10, 14],
                  "kick_amp": 0.18, "snare_amp": 0.0, "hat_amp": 0.055},
    },
    # story: 落ち着いた, パッド中心, ドラムなし
    "story": {
        "bpm": 90, "prog": [(45, MIN), (41, MAJ), (48, MAJ), (43, MAJ)],
        "pad_amp": 0.34, "bass_amp": 0.22,
        "arp": {"steps_per_bar": 4, "pattern": [0, 2], "amp": 0.11,
                "tau": 0.30, "staccato": 0.95, "bright": 0.6},
        "drums": {"kick": [], "snare": [], "hat": [],
                  "kick_amp": 0.0, "snare_amp": 0.0, "hat_amp": 0.0},
    },
    # points: 軽快, スタッカートの 16 分アルペジオ
    "points": {
        "bpm": 110, "prog": [(41, MAJ), (48, MAJ), (50, MIN), (46, MAJ)],
        "pad_amp": 0.24, "bass_amp": 0.26,
        "arp": {"steps_per_bar": 16, "pattern": [0, 1, 2, 3, 2, 1], "amp": 0.15,
                "tau": 0.07, "staccato": 0.45, "bright": 1.2},
        "drums": {"kick": [0, 8], "snare": [], "hat": [2, 6, 10, 14],
                  "kick_amp": 0.16, "snare_amp": 0.0, "hat_amp": 0.06},
    },
    # quiz: タメる, ドラム強め, ハーモニックマイナーの V
    "quiz": {
        "bpm": 100, "prog": [(50, MIN), (46, MAJ), (43, MIN), (45, MAJ)],
        "pad_amp": 0.30, "bass_amp": 0.30,
        "arp": {"steps_per_bar": 8, "pattern": [0, 1, 2, 1], "amp": 0.13,
                "tau": 0.11, "staccato": 0.6, "bright": 0.8},
        "drums": {"kick": [0, 8, 10], "snare": [4, 12], "hat": [0, 2, 4, 6, 8, 10, 12, 14],
                  "kick_amp": 0.30, "snare_amp": 0.13, "hat_amp": 0.08},
    },
    # ending: 温かい, ソフトパッド + 穏やかなアルペジオ
    "ending": {
        "bpm": 85, "prog": [(43, MAJ), (50, MAJ), (52, MIN), (48, MAJ)],
        "pad_amp": 0.34, "bass_amp": 0.20,
        "arp": {"steps_per_bar": 8, "pattern": [0, 2, 1, 2], "amp": 0.13,
                "tau": 0.28, "staccato": 0.9, "bright": 0.5},
        "drums": {"kick": [], "snare": [], "hat": [],
                  "kick_amp": 0.0, "snare_amp": 0.0, "hat_amp": 0.0},
    },
}

SEAM_FADE = 0.25   # セクション継ぎ目のフェード秒
HEAD_FADE = 0.6    # 冒頭フェードイン秒
TAIL_FADE = 2.2    # エンディング後フェードアウト秒


def midi_hz(m: float) -> float:
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def place(buf: np.ndarray, sig: np.ndarray, start: int, pan: float = 0.0,
          amp: float = 1.0) -> None:
    """buf は (n, 2) float。等出力パンで加算。"""
    n = buf.shape[0]
    s0 = max(start, 0)
    s1 = min(start + sig.shape[0], n)
    if s1 <= s0:
        return
    sig = sig[s0 - start: s1 - start] * amp
    theta = (pan + 1.0) * (np.pi / 4.0)
    buf[s0:s1, 0] += sig * float(np.cos(theta))
    buf[s0:s1, 1] += sig * float(np.sin(theta))


def render_pad(buf: np.ndarray, start: int, dur: int, freqs: list[float],
               amp: float, sr: int = SR) -> None:
    """detune で L/R を広げたコードパッド (slower attack/release)。末尾は範囲クリップ。"""
    n = buf.shape[0]
    s0 = max(start, 0)
    s1 = min(start + dur, n)
    if s1 <= s0:
        return
    t = np.arange(dur) / sr
    atk = min(0.9, dur / sr * 0.35)
    rel = min(1.0, dur / sr * 0.4)
    env = np.ones(dur)
    na = max(1, int(atk * sr))
    nr = max(1, int(rel * sr))
    env[:na] = np.linspace(0.0, 1.0, na)
    env[dur - nr:] *= np.linspace(1.0, 0.0, nr)
    for ch, det in ((0, 1.0012), (1, 0.9988)):
        sig = np.zeros(dur)
        for f in freqs:
            fd = f * det
            sig += (np.sin(2 * np.pi * fd * t)
                    + 0.35 * np.sin(2 * np.pi * 2 * fd * t + 0.5)
                    + 0.12 * np.sin(2 * np.pi * 3 * fd * t + 1.0))
        sig = sig / (1.47 * max(1, len(freqs))) * env * amp
        buf[s0:s1, ch] += sig[s0 - start: s1 - start]


def render_pluck(buf: np.ndarray, start: int, dur: int, freq: float, amp: float,
                 tau: float, bright: float, pan: float, sr: int = SR) -> None:
    t = np.arange(dur) / sr
    env = np.exp(-t / max(tau, 1e-3))
    na = max(1, int(0.004 * sr))
    env[:na] *= np.linspace(0.0, 1.0, na)
    sig = (np.sin(2 * np.pi * freq * t)
           + bright * 0.40 * np.sin(2 * np.pi * 2 * freq * t)
           + bright * 0.18 * np.sin(2 * np.pi * 3 * freq * t))
    place(buf, sig * env / 1.58, start, pan=pan, amp=amp)


def render_bass(buf: np.ndarray, start: int, dur: int, freq: float, amp: float,
                sr: int = SR) -> None:
    t = np.arange(dur) / sr
    na = max(1, int(0.012 * sr))
    nr = max(1, int(0.06 * sr))
    env = np.ones(dur)
    env[:na] = np.linspace(0.0, 1.0, na)
    env[dur - nr:] *= np.linspace(1.0, 0.0, nr)
    sig = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * 2 * freq * t)
    place(buf, sig * env / 1.25, start, pan=0.0, amp=amp)


def render_kick(buf: np.ndarray, start: int, amp: float, sr: int = SR) -> None:
    dur = int(0.28 * sr)
    t = np.arange(dur) / sr
    f = 44 + 70 * np.exp(-t * 20)
    phase = 2 * np.pi * np.cumsum(f) / sr
    env = np.exp(-t / 0.085)
    env[:40] *= np.linspace(0.0, 1.0, 40)
    place(buf, np.sin(phase) * env, start, pan=0.0, amp=amp)


def render_snare(buf: np.ndarray, start: int, amp: float,
                 rng: np.random.Generator, sr: int = SR) -> None:
    dur = int(0.16 * sr)
    t = np.arange(dur) / sr
    noise = rng.standard_normal(dur)
    noise = np.diff(noise, prepend=0.0)  # 疑似ハイパス
    env = np.exp(-t / 0.05)
    tone = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.035)
    place(buf, (noise * 0.8 + tone) * env / 1.8, start, pan=0.05, amp=amp)


def render_hat(buf: np.ndarray, start: int, amp: float,
               rng: np.random.Generator, sr: int = SR) -> None:
    dur = int(0.05 * sr)
    t = np.arange(dur) / sr
    noise = rng.standard_normal(dur)
    noise = np.diff(noise, prepend=0.0)
    env = np.exp(-t / 0.018)
    place(buf, noise * env, start, pan=-0.05, amp=amp)


def render_mood(mood_name: str, length_sec: float, rng: np.random.Generator,
                sr: int = SR) -> np.ndarray:
    """1 セクション分 (length_sec) のステレオ BGM を生成。bar 番号は絶対時刻ベースで
    mod 進行長 → ループ/切り出しでも音楽が連続する。"""
    m = MOODS[mood_name]
    beat = 60.0 / m["bpm"]
    bar = 4 * beat
    n = int(length_sec * sr)
    buf = np.zeros((n, 2))
    n_bars = max(1, int(np.ceil(length_sec / bar)))

    arp = m["arp"]
    drums = m["drums"]
    for b in range(n_bars):
        root, qual = m["prog"][b % len(m["prog"])]
        b0 = int(b * bar * sr)

        # パッド: root+12 の 3 和音 + ルートのオクターブ上 (次のバーに少し食い込む)
        pad_freqs = [midi_hz(root + 12), midi_hz(root + 12 + qual[1]),
                     midi_hz(root + 12 + qual[2]), midi_hz(root + 24)]
        pad_len = int(bar * sr * 1.12)
        render_pad(buf, b0, pad_len, pad_freqs, amp=m["pad_amp"])

        # ベース: 1・3 拍目
        for hb in (0, 2):
            s = int((b * bar + hb * beat) * sr)
            d = int(beat * 1.9 * sr)
            render_bass(buf, s, d, midi_hz(root), amp=m["bass_amp"])

        # アルペジオ: steps_per_bar 刻みで pattern を巡回 (交互パン)
        step_len = bar / arp["steps_per_bar"]
        chord = [root + 24, root + 24 + qual[1], root + 24 + qual[2], root + 36]
        for i in range(arp["steps_per_bar"]):
            note = chord[arp["pattern"][i % len(arp["pattern"])]]
            s = int((b * bar + i * step_len) * sr)
            d = int(step_len * arp["staccato"] * sr)
            pan = 0.55 if i % 2 == 0 else -0.55
            render_pluck(buf, s, d, midi_hz(note), amp=arp["amp"],
                         tau=arp["tau"], bright=arp["bright"], pan=pan)

        # パーカッション (16 分グリッド)
        grid = bar / 16.0
        for st in drums["kick"]:
            render_kick(buf, int((b * bar + st * grid) * sr), amp=drums["kick_amp"])
        for st in drums["snare"]:
            render_snare(buf, int((b * bar + st * grid) * sr), drums["snare_amp"], rng)
        for st in drums["hat"]:
            render_hat(buf, int((b * bar + st * grid) * sr), drums["hat_amp"], rng)

    # セクション端のシームフェード
    nf = int(SEAM_FADE * sr)
    buf[:nf] *= np.linspace(0.0, 1.0, nf)[:, None]
    buf[n - nf:] *= np.linspace(1.0, 0.0, nf)[:, None]
    return buf


def main() -> int:
    ap = argparse.ArgumentParser(description="numpy 合成 BGM (セクション別ムード, フル尺 1 本)")
    ap.add_argument("--episode", default=None, help="ep01 など")
    ap.add_argument("--timing", default=None, help="timing.json パス (既定: audio/<ep>/timing.json)")
    ap.add_argument("--out", default=None, help="出力 WAV (既定: audio/<ep>/bgm.wav)")
    ap.add_argument("--sr", type=int, default=SR)
    ap.add_argument("--peak-db", type=float, default=-12.0, help="ピーク正規化dBFS (既定 -12)")
    ap.add_argument("--seed", type=int, default=20261114, help="パーカッション用乱数種")
    args = ap.parse_args()

    if not args.episode and not args.timing:
        ap.error("--episode か --timing は必須")
    timing_path = Path(args.timing) if args.timing else Path("audio") / (args.episode or "ep01") / "timing.json"
    out_path = Path(args.out) if args.out else timing_path.parent / "bgm.wav"
    timing = json.loads(timing_path.read_text())
    sr = args.sr

    total = float(timing["total_duration"])
    sections = timing.get("sections") or {}
    if not sections:
        raise SystemExit("timing.json に sections がありません")

    rng = np.random.default_rng(args.seed)
    buf = np.zeros((int(total * sr), 2))
    unknown = [s for s in sections if s not in MOODS]
    if unknown:
        print(f"[bgm] 未定義セクション → story ムードで代用: {unknown}")

    for name, span in sections.items():
        start, end = float(span["start"]), float(span["end"])
        length = max(1.0, end - start)
        mood = name if name in MOODS else "story"
        seg = render_mood(mood, length, rng, sr=sr)
        s0 = int(start * sr)
        s1 = min(s0 + seg.shape[0], buf.shape[0])
        buf[s0:s1] += seg[: s1 - s0]
        print(f"[bgm] {name:8s} {start:8.3f} → {end:8.3f}  ({length:7.3f}s, mood={mood})")

    # 冒頭フェードイン / 末尾フェードアウト
    nh = min(int(HEAD_FADE * sr), buf.shape[0] // 4)
    nt = min(int(TAIL_FADE * sr), buf.shape[0] // 4)
    buf[:nh] *= np.linspace(0.0, 1.0, nh)[:, None]
    buf[buf.shape[0] - nt:] *= np.linspace(1.0, 0.0, nt)[:, None]

    peak = float(np.max(np.abs(buf)))
    if peak < 1e-9:
        raise SystemExit("BGM が無音です")
    buf *= 10 ** (args.peak_db / 20.0) / peak

    pcm = (np.clip(buf, -1.0, 1.0) * 32767).astype("<i2")
    inter = pcm.reshape(-1).tobytes()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(inter)

    dur = buf.shape[0] / sr
    print(f"[bgm] 出力: {out_path}  ({dur:.3f}s @ {sr}Hz 16bit stereo, peak {args.peak_db}dB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
