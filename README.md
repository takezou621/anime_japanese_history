# anime_japanese_history — アニメ日本史ラボ

中学・高校受験対策のための日本史アニメ動画を、**AIエージェントチームが制作**するプロジェクトです。
Season 1 (全10話, 総尺97分) は **全項目 green で確定済み** (2026-11-16 qa-visual 最終検証)。

📺 チャンネル: **アニメ日本史ラボ** / シリーズ: **日本史はじめて物語**

## 成果物一覧 (Season 1 確定版)

| 成果物 | パス | 状態 |
|---|---|---|
| 本編 10話 (各 8:32-13:12, 1080p30, 35.2Mbps CBR, bt709) | `video/ep01-10_FINAL.mp4` | ✅ 全話 QC PASS |
| 総集編 (96.99分, タイトルカード+全10話) | `video/compilation_FINAL.mp4` | ✅ PASS-with-notes |
| クイズ Shorts 3本 (1080×1920 縦型) | `video/shorts_ep01/ep04/ep09_q01.mp4` | ✅ PASS-with-notes |
| 脚本 10件 (リライト版・reading完備) | `content/episodes/ep01-10/script.json` | ✅ 確定 |
| 背景 161枚 + キャラスプライト + UI | `assets/ep01-10/` | ✅ Muse納品版統合済み |
| 音声 (narration + BGM + mix) | `audio/ep01-10/` | ✅ 確定 (辞書 sha `1af04182d53c`) |
| サムネイル 10点 (1280×720) | `youtube/thumbnails/ep01_thumb.png` ほか | ✅ |
| YouTubeメタデータ 10件 | `youtube/ep01.yaml` ほか | ✅ |
| 品質スコア (8周検証履歴+実測値) | `reports/quality_scores_ep01-10.md` | ✅ 全項目 green |
| Known Issues (非ブロッキング) | `reports/known_issues_season1.md` | 3点 (次シーズン対象) |

## ドキュメント

| ドキュメント | 内容 |
|---|---|
| [docs/01_PLAN.md](docs/01_PLAN.md) | 企画書 (コンセプト/シリーズ構成/品質基準) |
| [docs/02_DESIGN.md](docs/02_DESIGN.md) | 技術設計 (script.json契約/ツール仕様/分担) |
| [docs/03_STYLE_GUIDE.md](docs/03_STYLE_GUIDE.md) | アート&サウンド スタイルガイド |
| [docs/04_WORKFLOW.md](docs/04_WORKFLOW.md) | **制作フロー & チェックリスト (最新)** |
| [docs/05_CUBIC_REVIEW.md](docs/05_CUBIC_REVIEW.md) | Cubic コードレビュー運用 |
| [docs/06_AI_GENERATION.md](docs/06_AI_GENERATION.md) | AI生成パイプライン (月$10予算ガード) — **参考 (PoC・アート生成は停止中)** |
| [docs/07_YOUTUBE_OPS.md](docs/07_YOUTUBE_OPS.md) | YouTube運営 (メタデータ/アップロード) |
| [docs/08_COMPILATION_SHORTS_PLAN.md](docs/08_COMPILATION_SHORTS_PLAN.md) | 総集編・Shorts 仕様 |
| [docs/09_API_AND_RATE_LIMITS.md](docs/09_API_AND_RATE_LIMITS.md) | **外部API利用とレート制限の注意事項 (最新)** |
| [docs/10_QUALITY_BENCHMARK.md](docs/10_QUALITY_BENCHMARK.md) | 品質ベンチマーク (測定可能な合格基準) |

## パイプライン (現行)

```
Muse 納品アート (assets/epNN/scenes_v2/ + characters_v2/sprites/)
        │  lead が assets/epNN/scenes|overlay/ へ統合 (同一名配置)
content/episodes/epNN/script.json   (writer: 脚本 — reading完備)
        │
        ├─→ tools/audio/make_narration.py     (VOICEVOX: 発音辞書587語適用 + timing.json)
        │     または gen_narration_unified.py (Gemini TTS 音声一致システム, Muse環境で実行)
        ├─→ tools/audio/make_bgm.py + make_mix.py  (セクション別BGM + ダッキング -18dB + loudnorm)
        │     → tools/audio/check_voice_consistency.py (音声一致ゲート)
        ├─→ tools/editor/assemble.py          (レイヤー合成 / 字幕[文節境界+辞書383語] / banner半透明 / QC)
        │     → video/epNN_FINAL.mp4 + epNN_QC.json (35.2Mbps CBR / bt709 / TPゲート内)
        ├─→ tools/editor/compile_compilation.py  (総集編: タイトルカード + concat -c copy)
        ├─→ tools/editor/make_shorts.py          (Shorts: 縦型リフレーム + テロップ + QC)
        └─→ tools/thumbnail.py + youtube/make_metadata.py  (運営素材)
              → youtube/upload.py (Data API v3 / 認証情報なしは dry-run)
```

## 技術スタック (現行)

- **音声 (標準)**: VOICEVOX engine (ローカル, 127.0.0.1:50021) — 発音辞書587語で全固有名詞の読みを制御
- **音声 (音声一致システム)**: Gemini TTS (`gemini-2.5-pro-preview-tts`, voices: Kore=先生 / Puck=マナブ)
  — 固定モデル/固定temperature/設定ハッシュによる混入防止ゲート。詳細は
  [docs/09_API_AND_RATE_LIMITS.md](docs/09_API_AND_RATE_LIMITS.md)
- **アート**: **Muse が納品** (フルカラーアニメ調背景 161枚 + キャラスプライト+表情差分4種)。
  DSH 内での絵の生成は停止 (ユーザー指示 2026-11-15)。文字主体 UI (keyword_card 等) のみ Pillow コード生成を維持
- **字幕**: sudachipy代替の自前形態素処理 + 内容語境界ルール + 辞書383語 (`content/subtitle_dictionary.txt`) + `@pattern \d+年` 数値トークン化
- **編集**: ffmpeg-full (レイヤー合成 / 35.2Mbps strict CBR [nal-hrd=cbr+filler] / bt709 / banner alpha 0.4 / ASS字幕焼き込み / loudnorm)
- **品質管理**: 自動QC (10項目: 尺/解像度/fps/コーデック/pix_fmt/音声/loudness/color/bit_rate/黒フレーム)
  + 独立検証者3体 (qa-visual / qa-audio / qa-content) による多角的検証 + 実測値の記録義務

## クレジット

- 音声: [VOICEVOX](https://voicevox.hiroshiba.jp/) (四国めたん / ずんだもん) / Gemini TTS (Google)
- アート: Muse (プロジェクト監督による生成・納品)
- イラスト・脚本・編集: 本プロジェクトのAIエージェントチーム
