# anime_japanese_history — アニメ日本史ラボ

中学・高校受験対策のための日本史アニメ動画を、**AIエージェントチームが完全自動で制作**するプロジェクトです。
企画・脚本・作画・音声・編集・YouTube運営素材まで、すべてAIが担当します。

📺 チャンネル: **アニメ日本史ラボ** / シリーズ: **日本史はじめて物語** (全10話, 各話5〜10分)

## 成果物 (エピソード1)

| 成果物 | パス |
|---|---|
| 最終動画 (575秒, 1080p30, -14.4LUFS) | `video/ep01_FINAL.mp4` |
| QCレポート (全項目PASS) | `video/ep01_QC.json` |
| 脚本 (19シーン / 104ビート / クイズ3問) | `content/episodes/ep01/script.json` |
| 背景16種 + キャラ立ち絵 + バッジ23種 | `assets/ep01/` |
| ナレーション104本 + BGM + ミックス | `audio/ep01/` |
| サムネイル (1280×720) | `youtube/thumbnails/ep01_thumb.png` |
| YouTubeメタデータ (チャプター/タグ/概要欄) | `youtube/ep01.yaml` |
| アップロードマニフェスト (dry-run) | `youtube/ep01_upload_manifest.json` |

## ドキュメント

- [docs/01_PLAN.md](docs/01_PLAN.md) — 企画書 (コンセプト/シリーズ構成/品質基準)
- [docs/02_DESIGN.md](docs/02_DESIGN.md) — 技術設計 (script.json契約/ツール仕様/分担)
- [docs/03_STYLE_GUIDE.md](docs/03_STYLE_GUIDE.md) — アート&サウンド スタイルガイド
- [docs/04_WORKFLOW.md](docs/04_WORKFLOW.md) — 制作フロー & チェックリスト

## パイプライン

```
content/episodes/epNN/script.json   (writer: 脚本)
  → tools/audio/make_narration.py   (audio: VOICEVOX音声 + timing.json)
  → tools/audio/make_bgm.py + make_mix.py  (BGM合成 + -14LUFSミックス)
  → tools/art/generate_assets.py    (artist: 背景/キャラ/バッジ生成)
  → tools/editor/assemble.py        (editor: モーション/字幕/xfade/QC)
  → video/epNN_FINAL.mp4 + video/epNN_QC.json
  → tools/thumbnail.py + youtube/make_metadata.py (lead: 運営素材)
  → youtube/upload.py               (Data API v3 / 認証情報なしはdry-run)
```

## 技術スタック

- **音声**: VOICEVOX engine (四国めたん=ヒスト先生 / ずんだもん=マナブ, キャラ設定はオリジナル)
- **作画**: Python + Pillow (アニメ調フラットアート, スーパーサンプリング, 完全コード描画)
- **編集**: ffmpeg (zoompan Ken Burns / xfade / ASS字幕焼き込み / loudnorm 2パス)
- **品質管理**: 自動QC (長さ/解像度/ラウドネス/黒フレーム) + lead目視検収

## クレジット

- 音声: [VOICEVOX](https://voicevox.hiroshiba.jp/) (四国めたん / ずんだもん)
- イラスト・脚本・編集: 本プロジェクトのAIエージェントチーム
- [docs/05_CUBIC_REVIEW.md](docs/05_CUBIC_REVIEW.md) — cubic AI自動レビューの運用ガイド
