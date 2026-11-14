# YouTube 運営設計 — アニメ日本史ラボ

## 公開スロット (固定)

| 項目 | 値 |
|---|---|
| 公開曜日・時刻 | **毎週土曜 19:00 (JST)** |
| 本編 | 常時公開 (public) |
| Shorts | 本編公開の翌日 12:00 (JST) に週2本ずつ公開 |

- upload.py の `--publish-at` に JST ISO8601 を渡すと予約公開 (publishAt) になる
- 例: `--publish-at 2026-11-21T19:00:00+09:00`

## 再生リスト設計

| 再生リスト | 構成 | 目的 |
|---|---|---|
| **日本史はじめて物語 (全10話)** | ep01〜ep10 を時代順 | シリーズ視聴導線 |
| **日本史のすべて【総集編】** | 総集編1本 (60-70分) | 試験直前のまとめ視聴 |
| **一問一答クイズ Shorts** | クイズShorts全本 | すきま学習・拡散 |
| **受験ポイントまとめ** | 各話の「受験ポイントまとめ」セクション開始時刻から (chapter ではなく将来の個別切り出し用) | 直前対策 |

- youtube/playlists.yaml に定義 → upload.py の `--playlist` で追加
  (playlistItems.insert は要 YouTube Data API 認証、dry-run では manifest に記録)

## タイトル型 (全話統一)

```
【第N話】{フック質問 or 数字}{時代名}を5分で解説【中学受験日本史】
```

- 検索語 (時代名 / 日本史 / 中学受験) を必ず含める
- 話数番号 (第N話) はシリーズ視聴とプレイリスト並び順の指標

## 終了画面 (ending 構成)

各話 ending セクションの最終 15 秒:
1. 「次回 第N+1話 {タイトル}」カード (artist 生成の bg_next_episode + overlay_text)
2. 「チャンネル登録お願いします!」テロップ (subscribe_banner スタイル)
3. 直前の受験ポイント 1 行サマリ

→ script.json の ending セクション最終ビートに overlay_text で指定
  (next_episode_card / subscribe_banner スタイルは editor で実装)

## Shorts 計画

- 各話のクイズシーン (3問) から一問一答形式を切り出し、**最低 3 本 (30問中) を制作**
- フォーマット: 1080x1920 縦型 / 問題3秒→選択肢5秒→解答5秒→1行解説5秒 (計18秒前後)
- 切り出し元は ep01 / ep04 / ep08 (頻出度の高い時代) を優先
- 制作: tools/editor/make_shorts.py (quiz シーン抽出 + 縦型リフレーム + テロップ)
