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

### artist
- [ ] artlib が import できサンプル1枚が 1920×1080 で出る
- [ ] epNN の全 scene.background が生成済み (欠けゼロ)
- [ ] キャラ立ち絵: tools/peeps/compose_peeps.py 出力を使用 (artlib character.py は非推奨)
- [ ] カラーパレット・フォントは STYLE_GUIDE 準拠
- [ ] 各話専用 bg_timeline (時代アイコン+ラベル付き)

### audio
- [ ] make_narration.py が script.json → wav + timing.json を出す
- [ ] 発音: pronunciation_dict.json 自動置換 + pronunciation_log.json を出力し未カバー固有名詞ゼロ
- [ ] VOICEVOX 未起動時は自動起動 (vv-engine/run) する fallback
- [ ] 総尺 ≤590s (QC上限600s), mix.wav が -14±1.5 LUFS (loudnorm で検証)

### editor
- [ ] assemble.py が script.json + timing.json + assets → フル動画
- [ ] 字幕 (行頭禁則+ぶら下げ) ・モーション・クロスフェード確認
- [ ] キャラはコンテンツbbox基準配置 (CHAR_CONTENT_W=500, 下端930)
- [ ] QC json 出力 (長さ300-600s / ラウドネス / 黒フレーム<1% / 解像度)

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
- [ ] **視覚ゲート**: qa-visual がサンプルフレーム10枚以上で構図・文字かぶり・見切れゼロ
- [ ] サムネイル文字12文字以内 + キャラ視線が見出し側
- [ ] タイトルに話数番号+検索語 (時代名/日本史/中学受験) 含む
- [ ] 概要欄タイムスタンプが timing.json 実測と一致
