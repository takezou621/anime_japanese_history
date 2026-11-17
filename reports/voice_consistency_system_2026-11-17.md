# 声の一貫性システム（2026-11-17 制定）

## 背景
ep01 初版の音声は生成時の都合で3種類の TTS モデル（2.5-flash / 2.5-pro /
3.1-flash）を混用し、さらにビートごとに感情指示を変えていたため、
先生の声のイントネーションがビート間で揺れた。ユーザー指摘により、
一回限りの修正ではなく「仕組み」として以下を定める。

## ルール
1. モデルは全話・全ビートで1種類のみ（voice_config.json の model）。
   容量不足・障害時も別モデルへ切り替えず、待って同じモデルで再開する。
2. スタイルプロンプトはキャラクターごとに voice_config.json の文面を
   一字一句そのまま使う。ビートごとの感情指示（sentiment 等）は付けない。
3. 生成パラメータ（temperature 等）は voice_config.json で固定する。
4. 混在防止: 生成物は audio/<ep>/narration_unified/ に置き、manifest.json
   に設定ハッシュを記録する。ハッシュの異なる既存音声がある出力先では
   gen_narration_unified.py は中止する。
5. 生成後は check_voice_consistency.py のゲートを通す。全ビートの
   F0（中央値）と話速を測り、キャラクター中央値から F0 ±15% / 話速 ±25%
   を超えたビートは不合格とし、再生成するまで次工程へ進まない。

## 固定設定（voice_config.json）
- モデル: gemini-2.5-pro-preview-tts
- 先生: Kore / 「明るく優しい女性教師の声で、落ち着いて分かりやすく読み上げてください。」
- 学: Puck / 「元気で明るい少年の声で、はつらつと読み上げてください。」
- temperature: 0.7

## 手順
1. `uv run python tools/audio/gen_narration_unified.py --episode epNN`
   （audio/epNN/timing_unified.json も出力する）
2. `uv run --with numpy python tools/audio/check_voice_consistency.py --episode epNN`
   → GATE PASS を確認（レポート: audio/epNN/voice_consistency_report.json）
3. 不合格ビートは該当 WAV を消して 1 を再実行し、2 を通す。

## 注意
- gemini-3.8-flash-tts はスタイル指示を読み上げてしまうため使用禁止
  （従来からの既知事項）。
- VOICEVOX 時代の audio/<ep>/narration/ とは別系統。本システムの生成物を
  正とする。
