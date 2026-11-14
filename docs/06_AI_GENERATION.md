# AI 生成パイプライン — 月 $10 クレジット最適化 (tools/aigen)

Google AI Pro プラン特典の **月 $10 Google Cloud クレジット** の枠内で、
AI イラストと動画を最高品質で生成するための運用ドキュメント。

## 1. 基本戦略: 2段階パイプライン + 予算ガード

コスト消費が激しい動画生成での失敗 (ガチャ) をゼロにするため、
**「イラストで完璧な1枚を作ってから動画化する」2段階パイプライン** に徹する。

```
script.json (唯一の契約)
  → ① プロンプト設計   テキストモデル: シーン文脈+STYLE_GUIDE → 英プロンプト   (極小コスト)
  → ② 画像 draft       1K で構図を当てる (背景ごとに複数バリアント)          (安い)
  → ③ 人間が当たりを選ぶ (storyboard.html で目視)
  → ④ 画像 final       当たり1枚だけ 4K で再生成 (--same-prompt で同一プロンプト)
  → ⑤ adopt           1920×1080 に整形して assets/epNN/scenes/ へ採用 → editor は無変更
  → ⑥ (任意) Veo i2v   採用画像を開始フレームに渡して動画化。テキストからは作らない   (高価)
```

ガチャ防止の内訳:
- **テキストから直接動画を作らない** — 必ず確定済み画像を開始フレームとして渡す
- **draft (1K) → 選定 → final (4K)** — 構図の当たりが出てから高解像度に投資する
- **全呼び出し前に予算チェック** — 月間残高を超える見積もりは原則拒否 (`--force` で例外)

## 2. 月 $10 の予算配分 (1話あたりの目安)

| 項目 | 数量 | 単価 (目安) | 小計 |
|---|---|---|---|
| プロンプト設計 (テキスト) | ~40回 | $0.0005/回 | $0.02 |
| draft 画像 1K | 12背景×2枚 | $0.02/枚 | $0.48 |
| final 画像 4K | 12枚 | $0.12/枚 | $1.44 |
| Veo 動画 1080p | OP+ED 16秒 | $0.40/秒 | $6.40 |
| **合計** | | | **~$8.3 / 月$10** |

動画を増やすより draft 枚数を増やす方が安い。動画は「映える1カット」だけに使う。

## 3. セットアップ (初回のみ)

1. **クレジット紐付け**: Google AI Studio / Google Developer Program 特典ページで
   Google AI Pro アカウントの API キー請求設定 (Billing) から、
   $10/月クレジットを有効化した GCP プロジェクトを紐付ける。
   Veo を Vertex AI で使う場合は同じプロジェクトで **Vertex AI API** を有効化。
2. **SDK**: `uv run --with google-genai python tools/aigen/cli.py ...`
   (Pillow は `adopt` のみ必要: `uv run --with pillow ...`)
3. **認証情報** (どちらか):
   ```bash
   export GEMINI_API_KEY="AIzaSy..."                # Gemini API 経由
   # または Vertex AI 経由 (Veo 推奨)
   export GCP_PROJECT_ID="your-pro-credit-project-id"
   export GCP_LOCATION="us-central1"
   ```

## 4. モデルIDについて (重要)

`tools/aigen/config.json` のモデルID (`gemini-4-argon` / `gemini-nano-banana-2.1` /
`veo-3.1-generate-001` / `gemini-omni-1.2-flash`) は参考資料由来の **要確認値** である。

- 実行前に `uv run --with google-genai python tools/aigen/cli.py models --remote` で
  実在ID一覧を取得し、config.json を修正すること
- 単価 (`pricing_usd`) も見積もり用の目安。正確な額は Google Cloud の請求画面で確認し、
  台帳の見積もり精度を上げるために随時修正する
- Nano Banana 系 (`generate_content`) と Imagen 系 (`generate_images`) は
  `models.image_api` で切り替える

## 5. CLI リファレンス

実行はすべて `uv run --with google-genai python tools/aigen/cli.py` から。
グローバルフラグ: `--dry-run` (API を叩かず計画のみ) / `--force` / `--yes` / `--config`。

| サブコマンド | 役割 | 課金 |
|---|---|---|
| `models` [--remote] | 設定ID・単価の表示 / 実在モデル一覧 | --remote で僅少 |
| `prompt RAW --mode image\|video` | プロンプト設計のみ | テキスト1回 |
| `image RAW --ep ep03 --name NAME [--tier draft\|final] [--variants N]` | イラスト生成 | draft 1K / final 4K |
| `image ... --prompt-file FILE` | 同一プロンプトで final 再生成 | 画像1枚 |
| `video IMG RAW [--seconds N] [--resolution 1080p\|4k] [--no-audio]` | 採用画像から Veo 動画化 | 秒単価 (高価, `$2`超は`--yes`必須) |
| `storyboard --ep ep03 [--variants 2] [--plan] [--only BG...]` | script.json の新規背景を一括 draft | 背景数×バリアント |
| `budget [--month YYYY-MM]` | 台帳・残高・実行可能枚数/秒数 | なし |
| `adopt FILE --ep ep03 --bg bg_xxx` | 当たりを 1920×1080 で scenes/ に採用 | なし |
| `selftest` | オフライン動作確認 (API 不要) | なし |

### ep03 (平安) での実行例

```bash
# 0. 計画と費用確認 (API 不要)
python tools/aigen/cli.py storyboard --ep ep03 --plan -v

# 1. 12背景 × 2バリアントの draft を一括生成 (~$0.49)
python tools/aigen/cli.py storyboard --ep ep03 --variants 2 --yes

# 2. assets/ep03/ai_drafts/storyboard.html を目視して当たりを決める

# 3. 当たりだけ 4K で final 再生成 (同一プロンプト, ~$0.12/枚)
python tools/aigen/cli.py image "採用" --ep ep03 --name bg_heian_capital \
    --tier final --prompt-file assets/ep03/ai_drafts/prompts/bg_heian_capital.txt

# 4. editor 契約 (1920×1080 PNG) で scenes/ へ採用 — assemble.py は無変更で使える
uv run --with pillow python tools/aigen/cli.py adopt \
    <final.png> --ep ep03 --bg bg_heian_capital

# 5. (任意) OP のヒーローショットだけ Veo で動画化 (~$3.20/8秒)
python tools/aigen/cli.py video assets/ep03/scenes/bg_heian_capital.png \
    "カメラがゆっくり前進、市中の人流れ、鴉が飛ぶ。環境音と雅楽の調べ" \
    --ep ep03 --seconds 8 --yes
```

## 6. 予算ガードの仕組み

- 台帳: `tools/aigen/state/usage.json` (git 対象外)。全 API 呼び出し後に
  見積金額を記録する
- 呼び出し前: `monthly_budget_usd` (既定 $10.0) − 当月消費 < 見積 なら
  **BudgetError** で拒否 (`--force` で例外)。動画は `$2` 超で `--yes` 確認も要求
- `budget` で残高と「残りで画像何枚/動画何秒」を出す
- 見積もりは `pricing_usd` の目安値に基づく。**実請求額とは必ず突き合わせ**、
  差分が出たら config を修正する

## 7. スタイル制約 (STYLE_GUIDE との整合)

プロンプト設計のシステム指示は docs/03_STYLE_GUIDE.md に合わせてある:

- アニメ調フラットアート / 指定パレット hex / 影は同系濃色フラット1色
- **画像内に文字・ロゴ・水印を描かない** (テキストは editor が上から合成する)
- **背景にキャラを描かない** (キャラ立ち絵は別レイヤーで合成するため)
- 画面中央左はタイトル/字幕バンドのためにシンプルに
- 動画プロンプトは「開始フレームの構図を維持」「微細な動きで破綻回避」

## 8. 制限・注意事項

- 生成画像の著作権・利用規約は Google の生成物ポリシーに従う。公開動画の
  概要欄には AI 生成利用を明記する方針で統一する
- キャラの一貫性は AI 側でなく**既存の立ち絵レイヤー合成**で担保する
  (AI 背景はキャラなし → artlib の `char_*` と矛盾しない)
- Veo の結果が得られずタイムアウトした場合も課金が発生している可能性があるため、
  台帳に `video_timeout` として記録する
- モデルの無償枠/レート制限に当たった場合は `models --remote` と config の
  `image_api` を見直す
