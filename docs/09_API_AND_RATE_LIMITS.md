# 外部API利用とレート制限 — 注意事項

本プロジェクトで利用する (または利用を検討した) 外部APIの構成・レート制限・
トラブルシュートの記録。**認証情報 (APIキー等) はリポジトリに置かない** —
Muse 側のクレデンシャルサロゲートまたは環境変数で供給する。

## 1. Gemini TTS (音声一致システム) — 使用中

実装: `tools/audio/gen_narration_unified.py` (Muse 環境で実行)
設定: `tools/audio/voice_config.json`

| 項目 | 値 |
|---|---|
| エンドポイント | `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` |
| モデル | `gemini-2.5-pro-preview-tts` (voice_config.json で固定) |
| ボイス | Kore (ヒスト先生) / Puck (マナブ) — prebuiltVoiceConfig |
| temperature | 0.7 固定 (ビートごとの感情指定はしない) |
| 認証 | Muse クレデンシャルサロゲート `custom.gemini-api` (host: generativelanguage.googleapis.com) |

### 音声一致 (voice consistency) の仕組み
- 1モデル・1ボイス・スタイルプロンプトを全話・全ビートで一字一句固定
- `voice_config.json` の SHA-256 ハッシュ (先頭16文字) を manifest に記録
- 出力先 (`audio/<ep>/narration_unified/`) に**異なる config hash の音声があれば生成を中止**
  (声質混入防止)
- 生成後 `check_voice_consistency.py` のゲートを通し、外れ値ビートは再生成

### レート制限と注意事項 (実障害からの教訓)
- **pro TTS モデルはレート制限が厳しい** (実測: 連続生成で 429 を受ける)
- 対応 (commit `d723f89` で確定):
  - **呼び出し間隔 10秒** を空ける (バースト禁止)
  - **429 バックオフ: 45秒 × attempt** (線形増加, 最大 8 リトライ)
- 1,458 ビート (全10話) の生成実績あり。**モデル切替は禁止** (音声一致が壊れるため、
  容量不足・障害時も同じモデルで待って再開する)
- 失敗時: リトライ上限到達で RuntimeError → 途中から再実行 (完成ビートはキャッシュ利用)

## 2. VOICEVOX (音声, 標準) — ローカル・制限なし

実装: `tools/audio/make_narration.py`

| 項目 | 値 |
|---|---|
| エンジン | ローカル (127.0.0.1:50021, 未起動時は自動起動) |
| 発音辞書 | `tools/audio/pronunciation_dict.json` (587語, sha `1af04182d53c`) |
| 置換ログ | `audio/<ep>/pronunciation_log.json` (全ビートの置換記録) |
| キャッシュ | WAV/辞書ハッシュ差分のみ再生成 |

- ローカル実行のため**レート制限なし**。ただし TTS 合成は CPU バウンド
  (1,458 ビートで約 20-40 分, 2系統並列で短縮可)
- 注意: ** VOICEVOX のキャラボイスは「あみたろの声質工房」等の規約に従う**
  (商用利用は VOICEVOX 利用規約の範囲内)

## 3. Gemini 画像/動画生成 (tools/aigen) — PoC・アート生成は停止中

実装: `tools/aigen/` (docs/06_AI_GENERATION.md 参照)

| 項目 | 値 |
|---|---|
| 用途 | 背景イラスト (Nano Banana 系) / 動画化 (Veo i2v) — **2026-11-15 から停止** |
| 予算ガード | 月 $10 (Google AI Pro クレジット)。全呼び出し前に見積もり照合、超過は拒否 |
| 環境変数 | `GEMINI_API_KEY` / `GCP_PROJECT_ID` / `GCP_LOCATION` (既定 us-central1) |
| ポーリング | 動画操作は `poll_interval_sec = 15` で完了待ち |

### 現状と注意事項
- **ユーザー指示 (2026-11-15) により、DSH 内での絵の生成は中止**。アートは Muse が
  `assets/epNN/scenes_v2/` と `assets/characters_v2/` に納品する (同一名配置)。
  tools/aigen は PoC 資料として参照可能だが、**本番フローでは使用しない**
- 予算ガードの考え方 (月$10 上限・事前見積もり拒否) は、将来 API を復活させる際の
  運用テンプレートとして維持
- 単価表は「目安」。実行前に `models --remote` 等で実在 ID/実際の単価を確認する

## 4. YouTube Data API v3 — アップロード (dry-run 運用)

実装: `youtube/upload.py`

| 項目 | 値 |
|---|---|
| 認証 | OAuth 2.0 (認証情報が無い場合は **dry-run** で manifest のみ出力) |
| レート制限 | デフォルト クォータ: **1日 10,000 units** (アップロード 1本 ≈ 1,600 units) |
| 注意 | 1日 6本程度で上限到達。連続アップロードはスプレッドシート等で残高管理を推奨 |
| playlists | `youtube/playlists.yaml` でプレイリスト割当を定義 |

- Season 1 のマニフェスト: `youtube/epNN_upload_manifest.json` (dry-run 出力)

## 5. Muse メディア生成 (アート原画) — 外部

- キャラ原画・表情差分は `assets/characters_v2/source/media-generation-*.webp` として
  Muse 側インフラで生成・納品される (DSH からは API を呼ばない)
- 納品フロー: Muse がファイル配置 → lead が git commit → editor が統合
- **納品物は必ずコミットして保全する** (未コミットのまま git 操作で消失した実例あり —
  2026-11-15 の scenes_v2 消失事故の教訓)

## 6. クレデンシャル運用ルール

1. **APIキー・トークンをリポジトリにコミットしない** (GitGuardian が検知する)
2. Gemini TTS は Muse サロゲート (`custom.gemini-api`) 経由 — キーの実体は Muse 側で管理
3. tools/aigen を使う場合のみ環境変数 (`GEMINI_API_KEY` 等) をシェルで設定
4. YouTube OAuth クレデンシャルは `youtube/` 外に置き、dry-run で動作確認してから実運用へ

## 7. トラブルシュート速見表

| 症状 | 原因 | 対処 |
|---|---|---|
| TTS で 429 が連発 | pro TTS のレート制限 | 呼び出し間隔 10s 確認 + バックオフ 45s×n で再開 (リトライは最大8) |
| TTS モデル切替の誘い | 容量不足/障害 | **切替禁止** — 同一モデルで待機・再開 (音声一致維持) |
| 生成中止「config hash 不一致」 | voice_config.json を変更した | 出力先をクリアするか、旧ハッシュの生成物を退避 |
| 画像/動画生成の課金超過拒否 | 月$10 予算ガード | config.json の予算を見直すか、当月の利用を待つ |
| YouTube upload が quota エラー | 日次 10,000 units 消耗 | 翌日まで待つ (日本時間 午前9時頃にリセット) |
| VOICEVOX 接続エラー | エンジン未起動 | make_narration の自動起動 fallback を確認 (vv-engine/run) |
