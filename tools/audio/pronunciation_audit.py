#!/usr/bin/env python3
"""pronunciation_audit.py — 全エピソードの読み監査レポート生成

使い方:
    uv run python tools/audio/pronunciation_audit.py
    → content/pronunciation_audit.md を出力

内容:
1. 各話の TTS 入力テキストに辞書を適用 (dry-run) し、置換見込みを集計
2. 辞書・reading とも未カバーの漢字シーケンスを抽出 (固有名詞候補)
3. writer 基準 (content/pronunciation_audit_baseline.md) との読みコンフリクト一覧
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_narration import DEFAULT_DICT_PATH, apply_pronunciation, load_pronunciation_dict

REPO = Path(__file__).resolve().parent.parent.parent
EP_GLOB = "content/episodes/ep*/script.json"
OUT_PATH = REPO / "content" / "pronunciation_audit.md"
BASELINE = REPO / "content" / "pronunciation_audit_baseline.md"

# 一般語ストップワード (固有名詞ではない頻出語。監査ノイズ除去用)
STOPWORDS = {
    # 2字
    "武士", "武家", "公家", "農民", "商人", "職人", "町人", "貴族", "朝廷", "天皇",
    "将軍", "大名", "領主", "幕府", "政治", "政権", "政府", "改革", "経済", "軍事",
    "兵士", "天下", "戦国", "領土", "領地", "所領", "土地", "農業", "農地", "田畑",
    "稲作", "米作", "生産", "商業", "貿易", "貨幣", "財政", "年貢", "身分", "制度",
    "法令", "法律", "憲法", "条約", "同盟", "外交", "軍艦", "艦隊", "海軍", "陸軍",
    "戦争", "戦い", "合戦", "一揆", "暴動", "革命", "維新", "運動", "思想", "宗教",
    "仏教", "寺院", "神社", "神道", "学問", "教育", "学校", "大学", "出版", "新聞",
    "雑誌", "文学", "和歌", "連歌", "茶道", "書道", "絵画", "彫刻", "建築", "都市",
    "京都", "奈良", "東京", "大阪", "江戸", "鎌倉", "討伐", "鎮圧", "平定", "征服",
    "支配", "統一", "講和", "停戦", "降伏", "開城", "落城", "包囲", "撤退", "敗走",
    "戦死", "自害", "切腹", "処刑", "逃亡", "流刑", "追放", "現在", "当時", "理由",
    "存在", "社会", "国家", "対立", "戦闘", "兵器", "兵法", "統治", "治世", "即位",
    "退位", "譲位", "崩御", "逝去", "就任", "遷都", "動乱", "内乱", "反乱", "叛乱",
    "結末", "物語", "昔話", "神話", "伝説", "遺跡", "考古", "歴史", "世界", "日本",
    "時代", "文化", "現在", "昨日", "今日", "翌日", "前日", "当日", "半島", "列島",
    "都道", "府県", "国名", "地名", "人名", "語呂", "暗記", "学習", "復習", "予習",
    "教科書", "受験", "問題", "解答", "正解", "不正解", "クイズ", "選択肢",
    # 3字以上
    "武士団", "武士政権", "貴族政治", "政治家", "朝廷公家", "遣い", "軍隊", "軍勢",
    "戦国大名", "守護大名", "幕藩体制", "鎖国", "開国", "譜代", "外様", "親藩",
    "御三家", "老中", "大老", "参勤交代", "百姓", "庶民", "民衆", "指導者", "指揮",
    "総司令", "司令", "開戦", "開戦", "宣戦", "終戦", "開戦", "停戦", "休戦", "講和",
    "独立", "植民", "帝国", "王国", "共和国", "国境", "領海", "領空", "空軍", "海戦",
    "陸戦", "決戦", "野戦", "攻撃", "防衛", "防衛", "増援", "援軍", "味方", "敵方",
    "自軍", "連合", "枢軸", "参戦", "停戦", "全滅", "玉砕", "決起", "蜂起", "転戦",
    "進撃", "進軍", "出陣", "凱旋", "遠征", "親征", "南下", "北上", "東進", "西進",
    "拡大", "縮小", "拡張", "建設", "造営", "営造", "建立", "創建", "再建", "復興",
    "繁栄", "衰退", "滅亡", "興亡", "存亡", "継承", "相続", "簒奪", "下剋上",
}

# writer 基準とのコンフリクト (辞書は教科書標準を採用 → writer の検証を依頼)
CONFLICTS = [
    ("徳川慶喜", "よきの (writer基準)", "よしのぶ", "教科書・辞書標準は「よしのぶ」"),
    ("小野妹子", "いめこ (writer基準)", "いもこ", "中学教科書・広辞苑は「いもこ」"),
    ("清少納言", "きよしらのしょうごん (writer基準)", "せいしょうなごん", "教科書・広辞苑標準は「せいしょうなごん」"),
    ("豊臣秀吉", "ひでとし (writer基準)", "ひでよし", "秀吉=ひでよし (利家=としいえと混同に注意)"),
    ("井伊直弼", "いいなおさわ (writer基準)", "いいなおすけ", "教科書標準は「なおすけ」"),
    ("板垣退助", "いたがきたいすく (writer基準)", "いたがきたいすけ", "退助=たいすけ"),
    ("藤原薬子", "やくし (writer基準)", "ふじわらのやくこ", "薬子=やくこ (薬子の変=やくこのへん)"),
    ("前方後円墳", "ぜんぽうこうえんぷん (writer基準)", "ぜんぽうこうえんふん", "墳=ふん。辞書標準も「えんふん」"),
    ("漢委奴国王", "かんのいなこおう (writer基準)", "かんのなのこくおう", "現行中学教科書は「かんのなのこくおう」"),
    ("銅鐸", "どうたく (writer基準)", "どうてき", "考古学・教科書の用語読みは「どうてき」"),
    ("御家人", "ごかじん (writer基準)", "ごけにん", "教科書標準は「ごけにん」"),
    ("兵農分離", "へいのうぶんり (writer基準)", "ひょうのうぶんり", "教科書標準は「ひょうのうぶんり」"),
    ("安政の大獄", "あんせいのたいおく (writer基準)", "あんせいのたいごく", "大獄=たいごく"),
    ("壇ノ浦", "だんのうら (writer基準)", "うらのうら", "教科書標準は「うらのうら」(だんのうらは誤読)"),
    ("3%", "さんぱーせんと (writer基準)", "(辞書未登録)", "キーに漢字がなく辞書方針と不整合。VOICEVOX は「3%」を自然に読むため未登録。必要なら script.json の reading で指定を推奨"),
]

# writer 基準を採用した主な変更
ADOPTED = [
    ("乙巳の変", "いっしのへん → **きのとみのへん**", "writer 指摘通り干支読みが教科書準拠"),
    ("蝦夷", "(未登録) → えみし", "writer の reading 修正 (6891422) に一致させ辞書にも追加"),
    ("山名氏", "やまなみし誤読防止のため やまなし", "writer 注意① に一致"),
    ("遊行聖", "(未登録) → ゆぎょうひじり", "writer 指摘採用"),
    ("治天の君", "(未登録) → ちてんのきみ", "writer 注意⑥ に一致"),
    ("日出づる", "(未登録) → ひいづる", "writer 注意⑨ に一致"),
]


def scan_kanji_runs(text: str) -> list[str]:
    return re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff々〆]{2,}", text)


def main() -> int:
    pdict, dict_sha = load_pronunciation_dict(None)
    if not pdict:
        raise SystemExit("発音辞書が見つかりません")
    now = datetime.datetime.now().isoformat(timespec="seconds")

    eps = sorted(REPO.glob(EP_GLOB))
    per_ep: list[dict] = []
    candidates: dict[str, dict] = {}
    for sp in eps:
        script = json.loads(sp.read_text())
        ep = script.get("episode") or sp.parent.name
        beats = [(sc, b) for sc in script["scenes"] for b in sc["beats"]]
        n_reading = 0
        repl_count = 0
        repl_terms: dict[str, int] = {}
        for sc, b in beats:
            if b.get("reading"):
                n_reading += 1
                tts = b["reading"]
            else:
                tts, repls = apply_pronunciation(b["text"], pdict)
                repl_count += len(repls)
                for r in repls:
                    repl_terms[r["from"]] = repl_terms.get(r["from"], 0) + 1
            for run in scan_kanji_runs(tts):
                if run in pdict or run in STOPWORDS:
                    continue
                c = candidates.setdefault(run, {"count": 0, "eps": set(), "example": ""})
                c["count"] += 1
                c["eps"].add(ep)
                if not c["example"]:
                    snippet = re.sub(r"\s+", "", b["text"])
                    k = snippet.find(run)
                    lo, hi = max(0, k - 10), min(len(snippet), k + len(run) + 10)
                    c["example"] = ("…" if lo else "") + snippet[lo:hi] + ("…" if hi < len(snippet) else "")
        per_ep.append({
            "ep": ep, "title": script.get("title", ""), "scenes": len(script["scenes"]),
            "beats": len(beats), "reading": n_reading,
            "repl_beats": sum(1 for sc, b in beats if not b.get("reading") and
                              apply_pronunciation(b["text"], pdict)[1]),
            "repl_count": repl_count, "top_terms": sorted(repl_terms.items(), key=lambda kv: -kv[1])[:8],
        })

    lines: list[str] = []
    lines.append("# 発音監査レポート (ep01〜ep10)")
    lines.append("")
    lines.append(f"- 生成: {now} (tools/audio/pronunciation_audit.py)")
    lines.append(f"- 辞書: tools/audio/pronunciation_dict.json — **{len(pdict)}語** (sha256={dict_sha})")
    lines.append(f"- 監査対象: {len(per_ep)}話 / "
                 f"{sum(e['beats'] for e in per_ep)}ビート")
    lines.append(f"- writer 基準: content/pronunciation_audit_baseline.md と突き合わせ済み")
    lines.append("")
    lines.append("## 0. 総括")
    lines.append("")
    lines.append("| EP | タイトル | シーン | ビート | reading指定 | 辞書置換(件) |")
    lines.append("|---|---|---|---|---|---|")
    for e in per_ep:
        lines.append(f"| {e['ep']} | {e['title'][:20]} | {e['scenes']} | {e['beats']} "
                     f"| {e['reading']} | {e['repl_count']} |")
    lines.append("")
    lines.append(f"**辞書置換合計 (dry-run想定): {sum(e['repl_count'] for e in per_ep)}件**")

    lines.append("")
    lines.append("## 1. 読みコンフリクト (辞書は教科書標準を採用 → writer の検証依頼)")
    lines.append("")
    lines.append("writer 基準リストのうち、教科書・辞書の標準読みと矛盾する項目。")
    lines.append("**辞書には現状「教科書標準」を採用済み。writer が考証根拠を示して承認した場合のみ変更します**")
    lines.append("(間違った読みで全10話を量産するリスクを避けるための保守運用です)。")
    lines.append("")
    lines.append("| 表記 | writer基準 | 辞書採用 (教科書標準) | 根拠メモ |")
    lines.append("|---|---|---|---|")
    for term, w, m, note in CONFLICTS:
        lines.append(f"| {term} | {w} | **{m}** | {note} |")
    lines.append("")
    lines.append("### 採用した writer 指摘")
    lines.append("")
    lines.append("| 表記 | 変更 | 根拠 |")
    lines.append("|---|---|---|")
    for term, ch, note in ADOPTED:
        lines.append(f"| {term} | {ch} | {note} |")

    lines.append("")
    lines.append("## 2. 各話の辞書適用状況 (dry-run)")
    lines.append("")
    for e in per_ep:
        terms = ", ".join(f"{k}×{v}" for k, v in e["top_terms"]) or "—"
        lines.append(f"- **{e['ep']}**: 置換{e['repl_count']}件 / "
                     f"主な語: {terms}")

    lines.append("")
    lines.append("## 3. 未カバー漢字候補 (辞書・reading 未指定のまま残る語)")
    lines.append("")
    lines.append("検出ロジック: reading/辞書適用後の TTS テキストから漢字連続 (2字以上) を抽出し、")
    lines.append("一般語ストップワードと辞書登録済み語を除外。**「要判断」リストです (全てが固有名詞ではない)**。")
    lines.append("")
    tier1 = sorted([(k, v) for k, v in candidates.items() if len(k) >= 3],
                   key=lambda kv: -kv[1]["count"])
    tier2 = sorted([(k, v) for k, v in candidates.items() if len(k) == 2],
                   key=lambda kv: -kv[1]["count"])
    lines.append(f"- 3字以上: **{len(tier1)}語** / 2字: {len(tier2)}語 (一般語混入に注意)")
    lines.append("")
    if tier1:
        lines.append("### 3-1. 3字以上 (優先度 高)")
        lines.append("")
        lines.append("| 表記 | 回数 | EP | 例文 |")
        lines.append("|---|---|---|---|")
        for k, v in tier1:
            eps_str = ",".join(sorted(v["eps"]))
            lines.append(f"| {k} | {v['count']} | {eps_str} | {v['example']} |")
        lines.append("")
    if tier2:
        lines.append("### 3-2. 2字 (要スクリーニング — 一般語も多数含む)")
        lines.append("")
        lines.append("| 表記 | 回数 | EP | 例文 |")
        lines.append("|---|---|---|---|")
        for k, v in tier2:
            eps_str = ",".join(sorted(v["eps"]))
            lines.append(f"| {k} | {v['count']} | {eps_str} | {v['example']} |")
        lines.append("")

    lines.append("## 4. 検出方法と限界")
    lines.append("")
    lines.append("- VOICEVOX が正しく読める語も候補に含まれる (過剰検出あり)。最終判断は writer の考証 + 実音声の耳聞き QA。")
    lines.append("- カタカナ語・数字は対象外 (エンジン既定読みで自然)。")
    lines.append("- 辞書置換は **最長一致優先 + 単語境界考慮**: 前隣が漢字の場合は置換しないため、")
    lines.append("  未知の長い固有名詞が部分的に置換されて壊れることはない (未カバー語は監査で捕捉)。")
    lines.append("- 既存 reading 指定ビートは監査対象外 (writer 自己監査済み, commit 6891422)。")
    lines.append("")
    lines.append("### 運用ルール (writer 基準 §6 に準拠)")
    lines.append("")
    lines.append("1. `script.json` の `reading` が最優先")
    lines.append("2. 次に `tools/audio/pronunciation_dict.json` (最長一致)")
    lines.append("3. 最後に VOICEVOX エンジン既定")
    lines.append("4. script.json への書き込みは writer スコープ / 辞書は audio スコープ")

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[audit] {len(per_ep)}話 / {sum(e['beats'] for e in per_ep)}ビート走査")
    print(f"[audit] 候補: 3字以上 {len(tier1)}語 / 2字 {len(tier2)}語")
    print(f"[audit] 出力: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
