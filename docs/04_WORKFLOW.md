# 制作フロー & エージェント運用手順

## 進行ルール

1. **契約は script.json**。仕様変更は lead が docs/02_DESIGN.md を更新してから全員に通知する。
2. 各エージェントは自分の Write Scope 外に書き込まない (docs/02_DESIGN.md §5)。
3. 作業は GitHub Issues で管理。着手時に自分を assignee にし、完了条件を満たしたら close。
4. 各ツールは「小さく作って通しテスト」: 音声は10秒・アセットは1枚・編集は10秒動画を
   まず作り、lead に見せてから量産する。
5. ブランチ: いじらない (直コミット可, 小さく細かく)。lead が最終 diff とテストを確認する。

## 開発チェックリスト

### writer
- [ ] script.json が docs/02_DESIGN.md スキーマに準拠 (JSON as-is, コメント禁止)
- [ ] ナレーション総文字数 ≈ 目標秒数 × 7.5 文字/秒 (VOICEVOX 実測で調整)
- [ ] 受験ポイント ≥3, クイズ 3問, 年号・人名は教科書準拠
- [ ] 読みにくい漢字は `reading` フィールドで読み指定

### artist
- [ ] artlib が import できサンプル1枚が 1920×1080 で出る
- [ ] ep01 の全 scene.background が生成済み
- [ ] キャラ立ち絵 2種 (透過PNG)
- [ ] カラーパレット・フォントは STYLE_GUIDE 準拠

### audio
- [ ] make_narration.py が script.json → wav + timing.json を出す
- [ ] VOICEVOX 未起動時は自動起動 (vv-engine/run) する fallback
- [ ] mix.wav が -14 LUFS (ffmpeg loudnorm で検証)

### editor
- [ ] assemble.py が script.json + timing.json + assets → 10秒テスト動画
- [ ] 字幕焼き込み・モーション・クロスフェード確認
- [ ] QC json 出力 (長さ/ラウドネス/黒フレーム)

## 最終受け入れ (lead)
1. video/ep01_FINAL.mp4 を再生確認 (長さ・音ズレ・文字かぶり・見切れ)
2. QC json 合格 + サムネ生成 + youtube/ep01.yaml メタデータ
3. GitHub Issues close + 次話の制作指示
