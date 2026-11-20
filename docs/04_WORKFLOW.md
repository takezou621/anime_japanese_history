# 制作フロー & エージェント運用手順

## 進行ルール

1. **契約は script.json**。仕様変更は lead が docs/02_DESIGN.md を更新してから全員に通知する。
2. 各エージェントは自分の Write Scope 外に書き込まない (docs/02_DESIGN.md §5)。
3. 作業は GitHub Issues で管理。着手時に自分を assignee にし、完了条件を満たしたら close。
4. 各ツールは「小さく作って通しテスト」: 音声は10秒・アセットは1枚・編集は10秒動画を
   まず作り、lead に見せてから量産する。
5. **コード変更 (tools/**, youtube/**, scripts/**) は必ず PR 経由**:
   featureブランチ → commit → push → `gh pr create` → **Cubic自動レビュー SUCCESS確定** →
   `gh pr merge --squash --delete-branch`。NEUTRAL/未確定のままマージしない (2026-11-15 運用強化)。
   docs/ の更新と生成物 (assets/audio/video) のコミットは直接可。
6. 外部API・有料サービスへの依存追加は禁止。提案は tools/proposals/ に置き lead 承認を得る。

## 開発チェックリスト

### writer
- [ ] script.json が docs/02_DESIGN.md スキーマに準拠 (JSON as-is, コメント禁止)
- [ ] ナレーション総文字数 = 生文字 2400〜2800 (TTS reading展開込み ≈1.2倍)
- [ ] characters: sensei 1.22 / manabu 1.22, 1ビート2文まで, シーン4〜6ビート
- [ ] 受験ポイント ≥3, クイズ 3問, 年号・人名は教科書準拠
- [ ] 読みにくい漢字は `reading` フィールドで読み指定 (pronunciation_dict と突合)

### artist (2026-11-15 以降: アート生成は Muse へ移行)
- [ ] ~~artlib での背景・プロップ生成~~ **中止** (Muse が scenes_v2 / characters_v2 を納品)
- [ ] Muse 納品アセットの統合: `assets/epNN/scenes_v2/` → `assets/epNN/scenes/` (同一名配置)
- [ ] キャラスプライト: `assets/characters_v2/sprites/` → `assets/epNN/overlay/` (900×1400 透過PNG, 同一名)
- [ ] **文字主体 UI (keyword_card / era_badge) のみ Pillow コード生成を維持**
  (日本語テキスト正確性重視。左右パディング最低 24px)
- [ ] 納品物は**必ずコミットして保全** (未コミットのまま git 操作すると消失する — 実例あり)

### audio
- [ ] make_narration.py が script.json → wav + timing.json を出す
- [ ] 発音: pronunciation_dict.json 自動置換 + pronunciation_log.json を出力し未カバー固有名詞ゼロ
  (確定辞書 sha `1af04182d53c` — 全ブランチ同一)
- [ ] VOICEVOX 未起動時は自動起動 (vv-engine/run) する fallback
- [ ] 総尺 ≤590s 目標 (QC上限 900s — 2026-11-16 ユーザー決定で 600→900 に拡張)
- [ ] mix.wav が -14±1.5 LUFS (loudnorm で検証) / alimiter で TP ≤ -1.0 dBTP
- [ ] 音声一致システム (Gemini TTS) を使う場合: gen_narration_unified.py の
  ギャップ・リトライ規約に従う (docs/09_API_AND_RATE_LIMITS.md §1)

### editor
- [ ] assemble.py が script.json + timing.json + assets → フル動画
- [ ] 字幕 (行頭禁則+ぶら下げ+内容語境界ルール+辞書383語) ・モーション・クロスフェード確認
- [ ] キャラはコンテンツbbox基準配置 (CHAR_CONTENT_W=500, 下端930)
- [ ] 字幕 MarginV 79 (通常) / 250 (points帯上) — banner は字幕表示中 alpha 0.4
- [ ] QC json 出力 (長さ300-900s / 35.2Mbps CBR / bt709 / TP≤-1.0dBTP / ラウドネス / 黒フレーム<1%)
- [ ] **duration = timing 一致を必検証** (±0.35s。FAIL なら次話に進まず停止 — 2026-11-16 P1 教訓)
- [ ] **レンダー中はブランチを固定** (切替で成果物不整合 — 監督指摘)

## 多角的検証ゲート (2026-11-15 ユーザー指示により必須化)

動画の完成判定の前に、**3角度の独立検証**をパスすること。検証は**制作チームとは
独立した専門エキスパートエージェント (qa-visual / qa-audio / qa-content) が実施**し、
レポートを reports/ に残す。

### 各動画生成直後の即時検証 (2026-11-15 追加)
1. editor が epNN をレンダーしたら、**直ちに** 3体のQAエージェントへ検証を依頼する
   (バッチまとめ検証はしない。1動画=1検証サイクル)
2. QAエージェントは reports/qa_<angle>_epNN.md を作成し、総合判定 (PASS /
   PASS-with-notes / FAIL) と所見 ([P1必須修正/P2推奨/P3任意]) を報告する
3. P1 が1件でもあれば該当箇所を修正して再レンダー → 再検証。
   PASS-with-notes は P2 の修正を計画に入れて次へ継続可。
4. 3角度すべて PASS で lead が最終検収 → 完了。

| 検証 | 担当 | 観点 | 手法 |
|---|---|---|---|
| **音声QA** | audio | 発音の正確さ (固有名詞の読み), ビート同期, ラウドネス | pronunciation_dict 照合 + timing.json 突合 + loudnorm 計測 |
| **視覚QA** | artist | キャラ構図の自然さ, 背景との調和, 文字かぶり・見切れ | サンプルフレーム目視検証 (各話10枚以上) |
| **教育内容QA** | writer | 年号・人名・事件の史実正確性, 受験ポイントの妥当性, クイズの正答 | script.json と timing.json/字幕の突合 + 教科書準拠チェック |

### 発音検証 (音声QAの中核)
1. 全固有名詞は `tools/audio/pronunciation_dict.json` (writer監査済み) か
   script.json の `reading` フィールドで読みを保証する
2. make_narration.py が置換ログ (`audio/epNN/pronunciation_log.json`) を出力し、
   音声QAが「未カバー固有名詞ゼロ」を確認する
3. 不自然な読みの報告があった場合は辞書を修正して音声を再生成する

### 運用ルール
- 検証で指摘された項目は Issue に起票し、修正 → 再検証のループで閉じる。
- 3角度すべての検証レポートが揃って lead が最終検収 → 完了。

## 最終受け入れ (lead)
1. video/epNN_FINAL.mp4 を再生確認 (長さ・音ズレ・文字かぶり・見切れ)
2. 3角度検証レポートの確認 + QC json 合格
3. サムネ生成 + youtube/epNN.yaml メタデータ + GitHub Issues close

### 公開前チェックリスト (全項目必須 — 2026-11-15 ユーザー指示)
- [ ] **考証ゲート**: qa-content が全 beats・exam_points・quiz の史実正確性を検証し P1 ゼロ
  (年代・人名・用語の誤記 — 例: 墾田永年私財法, 弥生時代開始年代)
- [ ] **発音ゲート**: qa-audio が VOICEVOX 実読み (audio_query kana) を検証し
  固有名詞誤読ゼロ (pronunciation_dict + script reading の両方を突合)
  + **ASR突合** (tools/qa/asr_check.py): 全体一致率ゲート 0.70 / ビート 0.60 未満は要確認
- [ ] **視覚ゲート**: qa-visual がサンプルフレーム10枚以上で構図・文字かぶり・見切れゼロ
- [ ] サムネイル文字12文字以内 + キャラ視線が見出し側
- [ ] タイトルに話数番号+検索語 (時代名/日本史/中学受験) 含む
- [ ] 概要欄タイムスタンプが timing.json 実測と一致
- [ ] VOICEVOX クレジットが概要欄に記載されている

## Season 1 確定フロー (2026-11-16 確定 — 参考手順)

Season 1 (全10話) で実施した確定手順。Season 2 でも同じ流れを使う。

### 1. アート統合 (Muse 納品 → DSH)
1. Muse が `assets/epNN/scenes_v2/` (1920×1080 PNG, 従来同名) と
   `assets/characters_v2/sprites/` (900×1400 透過PNG + `char_<name>_expr_<emotion>.png`) を納品
2. lead が統合: `scenes_v2/` → `scenes/` コピー (同一名で editor は無変更で参照) +
   スプライトを `assets/epNN/overlay/` へ展開 → **必ずコミット** (未コミット保全の教訓)
3. レイアウト調整は画像内容でなく配置・尺側で吸収する

### 2. 音声 (音声一致システム)
1. script 確定 → `gen_narration_unified.py` で全ビート生成 (ギャップ契約:
   ビート間 0.30 / シーン間 0.60 / セクション間 0.80 / テール 0.60 — 台詞分割前提の標準)
2. `check_voice_consistency.py` ゲート通過を確認
3. TTS レート制限時は docs/09 §1 の規約 (間隔10s / バックオフ45s×n) で待機再開

### 3. レンダー
1. editor が `assemble.py` で全話レンダー (レイヤー入力の重複統合版を使用 —
   同一画像の重複入力は framesync デッドロックの原因, commit 5657946)
2. **各話 duration = timing 一致を必検証** (FAIL なら次に進まず停止)
3. QC json (10項目) 全 PASS を確認

### 4. 検証と確定
1. qa-visual / qa-audio / qa-content の受け入れ基準で最終抜き打ち
   (qa-visual 基準: 字幕×banner重なり0 / 空ラベル0 / 用語またがり0 / 退行なし)
2. green 判定後: **実測値一覧 (尺/bitrate/LUFS/TP/字幕最大字数) を PR 本文に記載して Muse 再提出**
3. 非ブロッキング所見は reports/known_issues_seasonN.md に記録して繰り込み

### 運用で確立したルール (再発防止)
- QA の指摘は**実測値+フレーム証拠**で受け止める (記憶ベースの裁定は禁止 — 辞書/実取得で確定)
- 読みの対立は**辞書実取得 (kotobank 等 9辞典パターン)** で解決。記憶ベースの主張より実取得データを優先
- 生成物 (video/audio) は QC PASS を確認してから次の工程へ。FAIL を無視した連続進行は禁止
