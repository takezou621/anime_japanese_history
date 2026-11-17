"""Unified narration generator (voice consistency system).

Reads ALL generation settings from voice_config.json in this directory:
one fixed model, one fixed voice + verbatim style prompt per character,
fixed temperature. Per-beat sentiment/emotion is intentionally ignored.

Anti-mixing guard: outputs go to audio/<ep>/narration_unified/ together
with a manifest recording the config hash. If existing files in that
directory were produced under a different config hash, the run aborts.

Usage (repo root):
  uv run python tools/audio/gen_narration_unified.py --episode ep01
Requires the Gemini API credential surrogate (custom.gemini-api), same
as the other Muse-side tools; run from Muse's environment.
"""
import argparse, base64, hashlib, json, subprocess, sys, time
import urllib.request, wave
from pathlib import Path

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

HERE = Path(__file__).parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import make_narration as mn  # load_pronunciation_dict, apply_pronunciation, wav_duration, build_timing


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused")


def config_hash(cfg: dict) -> str:
    blob = json.dumps(cfg, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def tts_call(cfg: dict, text: str, voice: str, retries: int = 8) -> bytes:
    body = {"contents": [{"parts": [{"text": text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "temperature": cfg["temperature"],
                                 "speechConfig": {"voiceConfig": {
                                     "prebuiltVoiceConfig": {"voiceName": voice}}}}}
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{cfg['model']}:generateContent")
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"},
                                         method="POST")
            add_surrogate_to_request(req, "custom.gemini-api",
                                     allowed_hosts=["generativelanguage.googleapis.com"])
            with urllib.request.build_opener(NoRedirect).open(req, timeout=180) as resp:
                data = read_json_response(resp)
            return base64.b64decode(data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"  retry {attempt + 1}: {e}", flush=True)
            time.sleep(20 * (attempt + 1))
    raise RuntimeError(f"TTS failed after retries: {last}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True)
    args = ap.parse_args()
    ep = args.episode

    cfg = json.loads((HERE / "voice_config.json").read_text())
    chash = config_hash(cfg)
    script = json.loads((REPO / "content/episodes" / ep / "script.json").read_text())
    pdict, _ = mn.load_pronunciation_dict(str(HERE / "pronunciation_dict.json"))

    out_dir = REPO / "audio" / ep / "narration_unified"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    manifest = {"config_hash": chash, "model": cfg["model"], "beats": {}}
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        if old.get("config_hash") != chash and any(out_dir.glob("*.wav")):
            print("ABORT: existing narration_unified files were generated "
                  "under a different voice config. Clear the directory first.")
            return 2
        manifest = old

    beat_meta = []
    total_speech = 0.0
    for scene in script["scenes"]:
        sid = scene["id"]
        for bi, beat in enumerate(scene["beats"]):
            spk = beat["speaker"]
            v = cfg["voices"][spk]
            tts_text, _ = mn.apply_pronunciation(beat["text"], pdict)
            prompt = f"{v['style_prompt']}\n{tts_text}"
            name = f"{sid}_b{bi:02d}.wav"
            wav_path = out_dir / name
            if wav_path.exists() and wav_path.stat().st_size > 1000:
                dur = mn.wav_duration(wav_path.read_bytes())
                print(f"skip {name} {dur:.2f}s", flush=True)
            else:
                raw = tts_call(cfg, prompt, v["voice_name"])
                tmp = out_dir / f"tmp_{name}"
                with wave.open(str(tmp), "wb") as w:
                    w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
                    w.writeframes(raw)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp),
                                "-ar", "48000", "-ac", "1", str(wav_path)], check=True)
                tmp.unlink()
                dur = mn.wav_duration(wav_path.read_bytes())
                print(f"gen  {name} {dur:.2f}s [{spk}] {beat['text'][:24]}", flush=True)
                time.sleep(4.0)
            manifest["beats"][name] = {"speaker": spk, "config_hash": chash,
                                       "model": cfg["model"], "voice": v["voice_name"]}
            total_speech += dur
            beat_meta.append({"scene_id": sid, "section": scene["section"],
                              "speaker": spk, "wav": f"narration_unified/{name}",
                              "duration": dur, "text": beat["text"]})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    timing = mn.build_timing(script, beat_meta)
    (REPO / "audio" / ep / "timing_unified.json").write_text(
        json.dumps(timing, ensure_ascii=False, indent=2))
    print(f"DONE beats={len(beat_meta)} speech={total_speech:.1f}s "
          f"total_duration={timing['total_duration']}s config={chash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
