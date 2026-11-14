# 技術設計書 — 制作パイプライン

## 1. 全体アーキテクチャ

```
content/episodes/ep01/script.json   ← writer (脚本)
        │
        ├──→ tools/audio/make_narration.py   ← audio agent
        │        → audio/ep01/narration/*.wav + timing.json (実音声長)
        │        → audio/ep01/bgm.wav (numpy合成BGM)
        │        → audio/ep01/mix.wav (ナレ+BGMミックス, -14 LUFS)
        │
        ├──→ tools/artlib + tools/art/generate_assets.py  ← artist agent
        │        → assets/ep01/scenes/*.png (1920×1080シーン絵)
        │        → assets/ep01/overlay/*.png (キャラ・小物・バッジ透過PNG)
        │
        └──→ tools/editor/assemble.py   ← editor agent
                 → 各シーンを動画セグメント化 (zoompan/motion)
                 → セグメント連結 + クロスフェード
                 → ミックス音声と結合 + 字幕焼き込み + loudnorm
                 → video/ep01_FINAL.mp4
```

**原則**: `script.json` が唯一の契約 (Single Source of Truth)。全ツールはこれを読む。

## 2. script.json スキーマ (v1)

```jsonc
{
  "episode": "ep01",
  "series": "日本史はじめて物語",
  "title": "日本の歴史、ここから始まる!〜縄文・弥生・古墳〜",
  "youtube": {
    "description": "...",   // 概要欄 (クレジット含む)
    "tags": ["日本史", "中学受験", "..."],
    "thumbnail": { "headline": "縄文×弥生×古墳", "sub": "受験必須!" }
  },
  "characters": [
    { "id": "sensei", "name": "ヒスト先生", "voice_style": "四国めたん/ノーマル",
      "speed_scale": 1.05, "pitch": 0.0, "subtitle_color": "#7ec8e3" },
    { "id": "manabu",  "name": "マナブ", "voice_style": "ずんだもん/ノーマル",
      "speed_scale": 1.08, "pitch": 0.0, "subtitle_color": "#8be27e" }
  ],
  "scenes": [
    {
      "id": "s01",
      "section": "opening",            // opening|story|points|quiz|ending
      "duration_hint_sec": 20,          // 目安 (実音声長を優先)
      "visual": {
        "background": "bg_school_lab",  // assets/ep01/scenes/ 内の名前
        "assets": [                     // レイヤー順 (下→上)
          { "name": "char_sensei", "pos": [1450, 380], "scale": 1.0,
            "motion": "slide_in_right" },
          { "name": "char_manabu", "pos": [330, 420], "scale": 1.0,
            "motion": "pop_in" }
        ],
        "camera": { "motion": "kenburns_in", "intensity": 1.0 }
      },
      "beats": [                        // 発話 = 音声セグメント (この順で再生)
        { "speaker": "sensei",
          "text": "こんにちは!ヒスト先生です。",
          "overlay_text": [ { "text": "アニメ日本史ラボ", "style": "title_main",
                              "motion": "fade_up" } ] },
        { "speaker": "manabu",
          "text": "今日は日本のはじまりを学ぶのだ!" }
      ],
      "exam_points": []                 // セクション points で使用
    }
  ],
  "quiz": [ { "q": "…?", "choices": ["ア","イ","ウ"], "answer": 1, "explain": "…" } ]
}
```

### ルール
- `beats[].text` がそのまま TTS 入力。読みが変になる箇所は漢字表記を調整する (音声用に `reading` フィールド可)。
- 音声長は実測で決まるため、シーン長 = Σ(音声長 + ギャップ0.6s)。`duration_hint_sec` は BGM とビジュアル計画の目安のみ。
- `overlay_text.style` は STYLE_GUIDE の定義を使う (title_main / era_badge / keyword_card / exam_banner / subtitle など)。

## 3. 各ツール仕様

### tools/audio/make_narration.py
1. script.json → VOICEVOX HTTP API (127.0.0.1:50021) でセグメント WAV 生成
   - speaker UUID は `/speakers` から動的解決 (スタイル名一致)
   - query パラメータ: speedScale/pitch/volumeScale をキャラ設定から反映
2. `timing.json`: 各シーン各ビートの開始時刻 (秒, 小数3桁) — editor が同期に使用
3. BGM: numpy 合成 (コードパッド + 軽いパーカッション), セクション別ムード
   - opening: 明るい / story: 落ち着き / points: 軽快 / quiz: タメ / ending: 温かい
4. mix: ffmpeg でナレ+BGM (-18dB) → `loudnorm=I=-14:TP=-1.5:LRA=11`

### tools/artlib (artist が実装するイラストライブラリ)
- Python + Pillow (+numpy)。スーパーサンプリング (2x描画→半縮小) でアンチエイリアス
- アニメ調フラットアートの部品: 空グラデ・山並み・家屋・土器・人物 (キャラ立ち絵)・地図 (日本列島パス)・タイムライン・巻物 UI など
- 部品を組み合わせて `generate_assets.py` が ep01 の全シーン PNG を出力
- フォント: Noto Sans JP (/Library/Fonts/NotoSansJP-{Regular,Bold,Black}.otf)
- **サムネイル用に文字入りバナーもここで生成**

### tools/editor/assemble.py
1. 各シーン: 背景PNG + レイヤー → ffmpeg zoompan / overlay でモーション付セグメント
   - motion 種類: kenburns_in/out, pan_l/r, slide_in_l/r, pop_in, fade
   - ビート開始時刻にレイヤー登場 (overlay enable='gte(t,X)')
2. セグメント連結: セクション跨ぎは 0.5s クロスフェード (xfade)
3. 字幕: timing.json から ASS 生成し焼き込み (縁取り, 話者色)
4. 音声: audio/ep01/mix.wav を mux → 最終 `video/ep01_FINAL.mp4`
5. 自動 QC: 長さ 300–600s, 平均ラウドネス, 黒フレーム率 < 1%, 解像度/ビットレート確認 → `video/ep01_QC.json`

## 4. リポジトリ構成

```
docs/            企画・設計・スタイルガイド・制作フロー
content/
  series.yaml    シリーズ全体 (10話)
  episodes/epNN/script.json
tools/
  artlib/        イラストライブラリ (artist)
  art/generate_assets.py   シーンレンダラー (artist)
  audio/         TTS/BGM/ミックス (audio)
  editor/        アセンブリ/QC (editor)
  thumbnail.py   サムネ生成 (lead)
  youtube/       メタデータ生成・アップロード (lead)
assets/epNN/     シーンPNG・レイヤー (artist 出力, git対象は軽量な再生成スクリプト優先)
audio/epNN/      narration/bgm/mix
video/           最終MP4 (大きいので .gitignore, QC json はコミット)
scripts/         開発用ユーティリティ
```

## 5. 並行作業の分担 (Write Scope)

| エージェント | スコープ | 担当Issue |
|---|---|---|
| lead | docs/, scripts/, youtube/, 全体統合・QC | #1 #7 #8 |
| writer | content/** | #2 |
| artist | tools/artlib/, tools/art/, assets/** | #3 #5 |
| audio | tools/audio/, audio/** | #4 |
| editor | tools/editor/, video/** | #6 |

**依存**: #2 脚本 → (#4 音声, #5 アセット) → #6 編集 → #8 最終QC。
ライブラリ実装 (#3/#4/#6) は script.json なしで先行開発可 (スキーマは本書が契約)。

## 6. 環境 (実測済み)

- ffmpeg 9.0.2 / Python 3.15 (uv, pillow, numpy OK) / VOICEVOX engine (127.0.0.1:50021, ヘッドレス起動済)
- フォント: NotoSansJP (Library/Fonts) + Hiragino
- YouTube: gh CLI 認証済み (repo 管理)。YouTube Data API 認証情報は現状なし → upload は dry-run 整備
