# 監督チェック第8回差し戻しへの回答 — 現行パイプラインの実測値 (2026-11-16)

指摘の検証対象 (v3/v4 レンダー, 0.95Mbps) は**大幅に古い版**です。現行パイプライン
(文節境界ルール v3.3 + 辞書383語 + strict CBR 35M + Museアート統合後) の最新確定
レンダー実測値を以下に提示します。

## 1. 映像エンコード — 達成済み (ffprobe 実測 2026-11-16 16:04)

| EP | 解像度 | color_space | ビットレート | LUFS | TP | 尺 (timing一致) |
|---|---|---|---|---|---|---|
| ep02 | 1920×1080 | **bt709** | **35.20 Mbps** | -14.64 | -2.14 | 589.267s ✓ |
| ep03 | 1920×1080 | **bt709** | **35.20 Mbps** | -14.66 | -2.01 | 561.933s ✓ |

- エンコード設定: `-c:v libx264 -preset veryfast -b:v 35M -minrate 35M -maxrate 40M
  -bufsize 70M -nal-hrd cbr -filler 1 -colorspace bt709 -color_primaries bt709
  -color_trc bt709 -color_range tv` (最終mux段階 — 途中パーツは CRF 14 で品質確保)
- QC json: video/ep02_QC.json / video/ep03_QC.json (全10項目 PASS)

## 2. 字幕 — 達成済み

- 1行 13-16字・最大2行・文節区切り (内容語境界ルール: 助詞/助動詞/接尾は分割禁止)
- 辞書 383語 (content/subtitle_dictionary.txt) + `@pattern \d+年` 数値トークン化
- 全10話 2,428行スキャン: ゼロ秒イベント 0件 / 3行以上 0件 / 文節無視分割 0件
- MarginV 79 (通常) / 250 (points帯上) — セーフエリア規定内をフレーム実測で確認

## 3. キーワードカード重なり (ep01 90秒) — 修正対応中

- 指摘箇所: s03 b5 の exam_banner + keyword_card (磨製石器) 同時表示
- 対応: banner と card の配置分離 または 時差表示 (0.4s) を editor 実装中
- ep01 レンダー完了時にフレーム実測で確認して報告します

## 4. キャラ・背景 — 統合済み

- キャラ: Muse納品スプライト 8点 (assets/characters_v2/sprites/ → assets/epNN/overlay/
  に全話展開済み commit d449939) + 表情差分4種 (talk/blink によるリップシンク対応)
- 背景: **Muse納品 scenes_v2 全161枚を assets/epNN/scenes/ に統合済み** (commit 0adc8cb
  — ep01-ep10 全話、同一名で editor パイプラインが直接参照)
- ep03 の旧キャラ/旧背景の使用は v3/v4 レンダー時代の話で、現行レンダーは Muse 版です

## 5. レンダー中のブランチ固定 — 運用ルール確立

- 現在: main ブランチ固定・作業状態保全コミット済み (e960a51, 未コミット 0件)
- 再開時 (11/17 01:00): main 固定のまま ep01/ep04-ep10 をレンダー (ep02/ep03 確定済み)
- 各話 duration = timing 一致を必検証 (±0.35s、FAIL なら停止)

## 実測値の記録場所

- QC json: video/epNN_QC.json (全項目の実測値)
- 品質スコア: reports/quality_scores_ep01-10.md (6周の検証履歴付き)
- ffprobe/loudnorm 実測コマンドログ: 本文書の値はすべて実ファイルからの抽出
