# AI 生成パイプライン — 月 $10 クレジット最適化 (tools/aigen × editor 統合)

Google AI Pro 特典の **月 $10 Google Cloud クレジット** の枠内で AI イラストと動画を
最高品質で使うための運用ドキュメント。**既存の制作パイプラインに組み込まれており**、
AI を使わない従来フローは一切変更されない (後方互換)。

## 1. 全体アーキテクチャ (パイプライン統合)

```
content/episodes/epNN/script.json  (唯一の契約)
   │  visual.ai / visual.ai_clip を任意で追記 (docs/02_DESIGN.md §2.1)
   │
   ├─→ tools/aigen (lead, 月$10予算ガード)
   │     ① episode --ep epNN --images
   │        テキストモデルでシーン文脈+STYLE_GUIDE → 英プロンプト (極小コスト)
   │        → draft 1K を assets/epNN/ai_drafts/ へ (バリアント複数)
   │        → storyboard.html で目視選定 → adopt で scenes/<bg>.png 採用
   │     ② episode --ep epNN --clips
   │        採用済み背景を開始フレームに Veo i2v (テキストから直接作らない)
   │        → video/epNN_ai/<sid>_<bg>.mp4 + manifest.json
   │
   └─→ tools/editor/assemble.py
         manifest.json / ai_clip にクリップがあるシーンは ai_segments.py が
         シーン長ちょうどに正規化 (トリム or 往復ループ) して背景動画に使用。
         字幕・キャラ合成・xfade は静画パスと同一。
         クリップ無し/失敗シーンは従来 kenburns に自動フォールバック
         (レンダーは落ちない, QC json の ai_segments に記録)
         → video/epNN_FINAL.mp4 + epNN_QC.json
```

ガチャ (動画の失敗) をゼロにする仕組み:
1. **テキストから直接動画を作らない** — 必ず採用済み画像を開始フレームとして渡す
2. **draft (1K) → 人間が選定 → final (4K)** — 当たりが出てから高解像度に投資
3. **予算ガード** — 全 API 呼び出し前に見積もりを月間残高と照合し、超過は原則拒否
4. **フォールバック** — クリップが用意できなかったシーンは従来通りの kenburns で成立

## 2. 月 $10 の予算配分 (1話あたりの目安)

| 項目 | 数量 | 単価 (目安) | 小計 |
|---|---|---|---|
| プロンプト設計 (テキスト) | ~40回 | $0.0005/回 | $0.02 |
| draft 画像 1K | 12背景×2枚 | $0.02/枚 | $0.48 |
| final 画像 4K | 12枚 | $0.12/枚 | $1.44 |
| Veo 動画 1080p | OP/EDなど 16秒 | $0.40/秒 | $6.40 |
| **合計** | | | **~$8.3 / 月$10** |

動画を増やすより draft 枚数を増やす方が安い。動画は「映える数カット」だけに使う。

## 3. セットアップ (初回のみ)

1. **クレジット紐付け**: Google AI Studio / Google Developer Program 特典ページで
   API キーの請求設定 (Billing) から $10/月クレジットを有効化した GCP プロジェクトを
   紐付ける。Veo を Vertex AI で使う場合は同じプロジェクトで Vertex AI API を有効化
2. **SDK**: `uv run --with google-genai python tools/aigen/cli.py ...`
3. **認証情報** (どちらか):
   ```bash
   export GEMINI_API_KEY="AIzaSy..."                # Gemini API 経由
   # または Vertex AI 経由
   export GCP_PROJECT_ID="..."  GCP_LOCATION="us-central1"
   ```

## 4. モデルIDについて (重要)

`tools/aigen/config.json` のモデルIDは参考資料由来の **要確認値**。
実行前に `uv run --with google-genai python tools/aigen/cli.py models --remote`
で実在ID一覧を取得し config.json を修正。単価 (`pricing_usd`) も実請求と突き合わせて
随時補正する。Nano Banana 系 (generate_content) / Imagen 系 (generate_images) は
`models.image_api` で切替。

## 5. 使い方 (ep 流れ)

```bash
AI="uv run --with google-genai python tools/aigen/cli.py"

# 0. 計画と費用確認 (API 不要)
$AI episode --ep ep03 --plan

# 1. 画像: draft 一括生成 → ai_drafts/storyboard.html で選定 → 採用
$AI episode --ep ep03 --images --variants 2 --yes
uv run --with pillow python tools/aigen/cli.py adopt \
    assets/ep03/ai_drafts/bg_heian_capital_1K_v1.png --ep ep03 --bg bg_heian_capital
# 当たりだけ 4K で final 再生成する場合
$AI image "採用" --ep ep03 --name bg_heian_capital --tier final \
    --prompt-file assets/ep03/ai_drafts/prompts/bg_heian_capital.txt

# 2. 動画: script.json の visual.ai.video シーンを Veo i2v で一括生成
#    (開始フレーム = 採用済み scenes/<bg>.png, manifest.json を更新)
$AI episode --ep ep03 --clips --yes

# 3. 動画生成 (manifest を読んで AI シーンのみ i2v, 其れ以外は kenburns)
uv run --with pillow python tools/editor/assemble.py --episode ep03
# QC json の "ai_segments" で used/fallback を確認
```

単発コマンド: `storyboard` (背景一括draft) / `image` / `video` / `adopt` /
`budget` (残高と実行可能枚数・秒数) / `models` / `prompt` / `selftest`。

## 6. 予算ガードの仕組み

- 台帳 `tools/aigen/state/usage.json` (git 対象外) に全呼び出しの見積金額を記録
- 呼び出し前: `monthly_budget_usd` (既定 $10) − 当月消費 < 見積 → **拒否** (`--force` で例外)
- 動画は $2 超で `--yes` 確認も要求。タイムアウト時も課金発生の可能性があるため
  台帳に `video_timeout` として記録
- `budget` サブコマンドで「残りで画像何枚 / 動画何秒」を表示

## 7. スタイル制約 (STYLE_GUIDE との整合)

- アニメ調フラットアート / 指定パレット hex / 影は同系濃色フラット1色
- **画像内に文字・ロゴ・水印を描かない** (テキストは editor が上から合成)
- **背景にキャラを描かない** (キャラ立ち絵は別レイヤー合成で一貫性を担保)
- 画面中央左はタイトル/字幕バンドのためシンプルに
- 動画プロンプトは「開始フレームの構図を維持」「微細な動きで破綻回避」
- i2v クリップの音声は使わない (デフォルト audio=false, ナレ/BGM は mix.wav 側)

## 8. 検証 (オフライン, API 不要)

```bash
python3 tools/aigen/cli.py selftest          # 単体 61項目
python3 tools/editor/ai_segments.py          # クリップ正規化 (trim/pingpong)
uv run --with pillow python tools/aigen/e2e_test.py   # aigen↔assemble 通し
```

E2E は偽クリップ (ffmpeg testsrc2) で「AIシーン使用 / 欠損フォールバック /
字幕オーバーレイ / xfade / QC」まで検証する。

## 9. 制限・注意事項

- 生成物の利用は Google の生成物ポリシーに従う。概要欄に AI 生成利用を明記
- `visual.ai` を書かないエピソードは従来フローのまま (パイプラインは無 changes)
- Veo レート制限に当たったら `models --remote` と `image_api` を見直す
