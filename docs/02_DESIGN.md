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

### §2.1 AI 生成指定 (v1.1 追記 — 任意, 後方互換 / lead 2026-11-14)

既存フィールドは一切変更しない。AI 生成を使うシーンだけ `visual` に `ai` を追記する:

```jsonc
"visual": {
  "background": "bg_heian_capital",   // 従来どおり必須 (フォールバック & 動画の開始フレーム)
  "ai": {
    "image": { "hint": "夕暮れの朱雀大路、髪は静かに流れる...", "variants": 2, "tier": "draft" },
    "video": { "prompt": "ゆっくり前進、市中の人流れ、夕光の揺らぎ", "seconds": 8,
               "resolution": "1080p", "audio": false }
  }
}
```

- **生成運用は tools/aigen** が担当 (`episode --ep` / docs/06_AI_GENERATION.md):
  - 画像 → `assets/epNN/ai_drafts/` に draft (目視選定 → `adopt` で `scenes/` 採用)
  - 動画 → `video/epNN_ai/<sid>_<bg>.mp4` を Veo image-to-video で生成し
    `video/epNN_ai/manifest.json` (`{"clips": {"<sid>": "<file>"}}`) を更新
- **editor は assemble.py が自動で解決**:
  - manifest.json / `visual.ai_clip` (明示パス, こちら優先) にクリップがあるシーンは
    `ai_segments.py` がシーン長ちょうど (timing.json 実測) に正規化して使用する
    (クリップ > シーン長ならトリム、短ければ往復ループ — 静止3秒禁止を維持)
  - クリップが無い/壊れているシーンは**従来 kenburns に自動フォールバック**し、
    QC json の `ai_segments` に used/fallback を記録する (レンダーは落ちない)
- **予算**: tools/aigen/state/usage.json 台帳で月 $10 をガード (超過見積もりは拒否、
  `--force` で例外)。単価・モデルID は `tools/aigen/config.json` で管理

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
   - **AI i2v クリップ指定シーン** (§2.1): `ai_segments.py` が正規化したクリップを
     背景動画として使用。字幕/レイヤー合成・xfade は静画パスと同一。欠損時は
     kenburns にフォールバックし QC `ai_segments` に記録
   - ビート開始時刻にレイヤー登場 (overlay enable='gte(t,X)')
2. セグメント連結: セクション跨ぎは 0.5s クロスフェード (xfade)
3. 字幕: timing.json から ASS 生成し焼き込み (縁取り, 話者色)
4. 音声: audio/ep01/mix.wav を mux → 最終 `video/ep01_FINAL.mp4`
5. 自動 QC: 長さ 300–600s, 平均ラウドネス, 黒フレーム率 < 1%, 解像度/ビットレート確認 → `video/ep01_QC.json`

### tools/editor/ai_segments.py
- AI クリップの解決 (`visual.ai_clip` > `video/epNN_ai/manifest.json`) と正規化
- 正規化: scale/crop 1920×1080 → 30fps CFR → シーン長ちょうどへ
  (トリム or 往復ループ) → 無音 h264。`python3 tools/editor/ai_segments.py` で単体テスト
- 生成側の呼び出しは tools/aigen (下記) が担当し、editor は読むだけ

### tools/aigen (AI 生成 — lead, docs/06_AI_GENERATION.md)
- `cli.py episode --ep epNN`: script.json の `visual.ai` を読み
  画像 draft / Veo クリップ (+manifest) を一括生成。月 $10 予算ガード付き
- `cli.py storyboard|image|video|adopt|budget`: 単発操作。`cli.py selftest` /
  `e2e_test.py` は API 不要のオフライン検証
- モデルID・単価は `config.json` (実行前に実在IDの確認を推奨)

## 4. リポジトリ構成

```
docs/            企画・設計・スタイルガイド・制作フロー
content/
  series.yaml    シリーズ全体 (10話)
  episodes/epNN/script.json
tools/
  artlib/        イラストライブラリ (artist)
  art/generate_assets.py   シーンレンダラー (artist)
  aigen/         AI生成 (lead): 予算ガード/プロンプト設計/draft→final→採用/Veo i2v
  audio/         TTS/BGM/ミックス (audio)
  editor/        アセンブリ/QC (editor) — ai_segments.py は AI クリップ正規化
  thumbnail.py   サムネ生成 (lead)
  youtube/       メタデータ生成・アップロード (lead)
assets/epNN/     シーンPNG・レイヤー (artist 出力, git対象は軽量な再生成スクリプト優先)
  epNN/ai_drafts/ AI draft (git対象外, storyboard.html で選定)
audio/epNN/      narration/bgm/mix
video/           最終MP4 (大きいので .gitignore, QC json はコミット)
  epNN_ai/       Veo i2v クリップ + manifest.json (git対象外)
scripts/         開発用ユーティリティ
```

## 5. 並行作業の分担 (Write Scope)

| エージェント | スコープ | 担当Issue |
|---|---|---|
| lead | docs/, scripts/, youtube/, tools/aigen/, 全体統合・QC | #1 #7 #8 |
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
