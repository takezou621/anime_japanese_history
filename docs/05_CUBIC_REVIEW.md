# cubic AI レビュー運用ガイド

このリポジトリでは [cubic.dev](https://www.cubic.dev) による AI コードレビューを利用しています。

## 自動レビューの挙動

- PR を作成すると cubic が自動でレビューを開始します(数分で完了)
- PR にコミットを追加 push した場合も差分のみ追加レビューされます(`incremental_commits: true`)
- draft PR は自動レビューされません(`check_drafts: false`)

## 設定

設定はリポジトリルートの [`cubic.yaml`](../cubic.yaml) で管理しています。
cubic はデフォルトブランチ (`main`) の設定のみを読みます。

主な設定:

| 項目 | 値 | 説明 |
| --- | --- | --- |
| `reviews.enabled` | `true` | AI レビュー有効 |
| `reviews.incremental_commits` | `true` | push 追加分も自動レビュー |
| `reviews.check_drafts` | `false` | draft はスキップ |
| `reviews.ignore.files` | `*.wav` `*.mp4` 等 | 生成メディアのバイナリを対象外 |
| `reviews.ignore.pr_labels` | `skip-review` | このラベルで自動レビューをスキップ |
| `pr_descriptions.generate` | `true` | PR 概要の自動生成 |

## cubic との対話

- 指摘コメントに返信: `@cubic-dev-ai なぜこれが問題ですか?`
- 修正依頼: `@cubic-dev-ai これを修正してください`(PR ブランチに直接 push します)
- レビューの再実行: `@cubic-dev-ai review this PR`
- スキップ: PR に `skip-review` ラベルを付与

## 備考

- このリポジトリには CodeRabbit / GitGuardian も導入されています。重複指摘の際は `cubic.yaml` の `custom_instructions` で調整できます
- レビュー品質の学習: 指摘が不要な場合はスレッドで理由を返信すると cubic が学習します
