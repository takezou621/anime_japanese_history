# キャラスプライト修正 (2026-11-15, Muse 介入)

対象: `tools/peeps/compose_peeps.py`。DSH チーム向けの申し送り。

## 症状
- バストアップ生成で巨大な顔が胸の上に乗り、位置も左へずれていた
- 全身スプライトはキャンバス (900x1400) の縦約半分・中央浮きで、
  顔が想定位置より大きく下がっていた (QA の P1-1 の一因)

## 根本原因 (3件とも compose_peeps.py の実装バグ)
1. **バスト合成が全身用の固定値を流用**: `build_head_svg_bust` が
   頭部に `translate(225 0)` + `HEAD_SCALE=1.1` を適用。肩幅の広い
   バストポーズ (実測 792 units) に対し頭幅が 561 units になり、
   顎が襟ではなく胸の中央に落ちていた。
2. **place_on_canvas の SS 単位混同**: SS=2 のキャンバス (2800px) に
   最終解像度の 1380px でキャラを拡縮 → 縦半分サイズで中央配置。
3. **全身の OVERLAP 不足**: 40 ではポーズ側の首元シルエットが
   柱状に露出して顔が浮いて見えた。

## 修正内容
- `compose_bust()` を新設 (計測アラインメント方式):
  ポーズと頭部を別々にレンダリングして実測し、
  頭幅 = 肩幅の 44% / 顎位置 = ポーズ上端 + 高さの 16% /
  頭中心 = ポーズ最上部行 (首アンカー) の中心 で合成。
  合成時は頭の高さ分の余白キャンバスを使い頭頂の切り落としを防止。
  最後に 900x1400 へ正規化。`--mode bust` はこちらを使う。
- `place_on_canvas`: 目標高を `(H-20)*SS` に修正し下端アンカーに変更。
- `OVERLAP`: 40 → 110。

## 生成物 (再生成済み)
- 全10話 overlay: `char_sensei.png` / `char_manabu.png` (全身, 修正版)
  - 実測 alpha bbox: y 7..1393 (従来 352..1048)
- 全10話 overlay に追加: `char_sensei_bust.png` / `char_manabu_bust.png`
  - 900x1400, alpha bbox y 37..1070 / 37..1093、顔は上部に正常配置
  - 目視確認済み (先生=お団子+丸眼鏡+ボタンシャツ、マナブ=短髪+赤T)

## 再生成コマンド
```bash
uv run --with pillow python tools/peeps/compose_peeps.py --out assets/ep01/overlay
uv run --with pillow python tools/peeps/compose_peeps.py --mode bust --out assets/ep01/overlay
```

## 注意
- 本修正は未コミット (compose_peeps.py 変更 + assets 20件変更 + bust 20件追加)。
  取り込みはリードの判断で。元ファイルの控えは /tmp/compose_peeps.py.bak。
- ポーズ側の首元は単一パスの CLOTHES 塗りのため、色の付いた首が
  わずかに見えるのは素材仕様 (Open Peeps パーツ変換由来)。

## 追記 (2026-11-15): 向き合い原則の適用
- 指摘: 2人とも同じ方向 (右) を向いており、会話シーンとして不自然。
- 実測: 配置は全話固定 (マナブ=左、先生=右)。素材の顔は両者とも右向きで、
  右配置の先生が画面外を向いていた。
- 対応: compose_peeps.py に char_sensei の "flip": True を追加し、
  全10話の全身・バスト素材を反転生成し直した。2ショット合成で
  視線が向き合うことを目視確認済み。
- ルールは docs/03_STYLE_GUIDE.md「キャラの向き (向き合い原則)」に明文化。
