# tools/editor — アセンブリ & QC パイプライン (Issue #5)

`script.json + timing.json + assets/` から最終MP4とQCレポートを作る。

## 構成

| ファイル | 役割 |
|---|---|
| `assemble.py` | メイン。プラン→セグメント並列レンダー→xfade連結→字幕帯+字幕焼き込み→mux→QC |
| `motion.py` | zoompan kenburns / レイヤーモーションの ffmpeg 式ビルダー |
| `text_overlays.py` | overlay_text スタイル (STYLE_GUIDE) の PNG レンダラー + 字幕帯 |
| `make_subtitles.py` | timing.json + script.json → ASS (libass `subtitles` で焼き込み) |
| `qc.py` | QC (長さ/解像度/fps/ラウドネス/黒フレーム/ストリーム) → `video/epNN_QC.json` |
| `fixtures/` | 10秒テスト用モック (script_test.json, timing_test.json, make_fixtures.py) |

## 実行

```bash
# テスト (モック10シーン, 約12秒)
uv run --with pillow --with numpy python tools/editor/fixtures/make_fixtures.py
uv run --with pillow python tools/editor/assemble.py --episode ep00 --profile test \
  --script tools/editor/fixtures/script_test.json \
  --timing tools/editor/fixtures/timing_test.json \
  --assets tools/editor/fixtures/assets_test \
  --mix tools/editor/fixtures/mix_test.wav \
  --out video/ep00_TEST.mp4 --qc video/ep00_TEST_QC.json

# ep01 本番 (既定パスは規約どおりなら --episode だけでOK)
uv run --with pillow python tools/editor/assemble.py --episode ep01
# デバッグ: --dry-plan / --only-scenes s01,s02 / --keep-parts / --jobs 4
```

**ffmpeg要件**: libass (`subtitles` フィルタ) 必須。既定の brew ffmpeg 9.0.2 には
drawtext/subtitles が無いため、`ffmpeg-full` を自動検出する
(`/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg` → 無ければ PATH, `--ffmpeg` で明示可)。
ffmpeg 9 は `-filter_complex_script`/`-vsync` が削除済み → `-/filter_complex <file>`
と `-fps_mode` を使用。

## タイムライン設計 (字幕ズレ防止)

セクション跨ぎ境界だけ 0.5s xfade。境界に隣接するセグメントは head/tail に
0.5s の「借り」を持たせ、ブレンドを `[boundary-0.5, boundary)` に置くことで、
**最終動画のタイムライン = timing.json のタイムライン** (合計長も一致)。
字幕・レイヤー出現はグローバル時刻をそのまま使える。同セクション隣接はハードカット。

## timing.json 契約 (tools/audio が生成)

```jsonc
{
  "episode": "ep01",
  "total_duration": 575.561,
  "scenes": [
    { "id": "s01", "section": "opening", "start": 0.0,   // duration は省略可
      "beats": [ { "speaker": "sensei", "start": 0.0, "duration": 5.909,
                   "wav": "narration/s01_b00.wav", "text": "..." } ] }
  ]
}
```
- scene `duration` 省略時は「次シーンのstart」から導出 (最終シーンは total_duration)
- beats[].start はグローバル秒。`duration` があれば beat end に採用 (なければ次beat開始)
- ep01 実データ (19シーン, 575.561s) はこの形式 ✓

## editor 側の解釈ルール (lead 確認事項)

- `visual.assets[].pos` / `overlay_text[].pos` は **レイヤー中心** の 1920x1080 座標
- レイヤー出現時刻: アセット名がキャラidを含む (例 `char_sensei`→`sensei`)
  → その話者のシーン内最初のbeat開始。それ以外はシーン最初のbeat。同時刻は 0.25s ずつズらす
- `overlay_text` はその beat の開始時刻に登場 (同beat複数は 0.15s ずつズらす)
- 字幕帯は最終パスで overlay → 字幕 (libass) が常に最前面。exam_banner 等
  下端寄せスタイルの既定位置は帯 (top≈0.86h) の上 y=0.70h (lead v2 フィードバック)
- keyword_card は最小 520x140px を保証 (文字が少なくてもカードサイズは維持)
- motion 未指定時: レイヤー=`fade`, スタイル既定 (`STYLES[style]["default_motion"]`)
- モーション長 0.5s 固定 (STYLE_GUIDE 0.4–0.6s の中央), `dur` で上書き可
- 字幕: 52px Bold, ラベル=話者色+太字 / 本文=白, 黒フチ4px+影, 角丸半透明黒帯の上に焼き込み
  (lead フィードバック 2026-11-14)。折返し 22字/行・最大2行, 超過分は文分割で複数イベント化

## QC 基準 (video/epNN_QC.json)

- duration: timing.total_duration と ±0.35s。full プロファイルでは 300–600s も確認
- 1920x1080 / 30fps / h264 / yuv420p / aac
- loudness: -14 LUFS ±1.5, TP <= -1.0 (test プロファイルは warn のみ)
- blackdetect < 1%
