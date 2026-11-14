#!/usr/bin/env python3
"""月次予算台帳 + 見積もり.

Google AI Pro の月 $10 クレジットを守るため、全 API 呼び出し前に
見積もり金額を残高と照合し、超過見込みなら拒否する (BudgetError)。
実行結果は tools/aigen/state/usage.json に追記していく (git 対象外)。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import state_dir

USAGE_FILE = "usage.json"


class BudgetError(RuntimeError):
    """月間予算を超える見込みの呼び出し。"""


# ---------------------------------------------------------------- 見積もり

def est_image(cfg: dict, size: str, variants: int = 1) -> float:
    table = cfg["pricing_usd"]["image"]
    if size not in table:
        raise ValueError(f"不明な画像サイズ: {size} ({sorted(table)} から選択)")
    return round(table[size] * variants, 4)


def est_video(cfg: dict, seconds: float, resolution: str = "1080p",
              audio: bool = True) -> float:
    per_sec = cfg["pricing_usd"]["video_per_second_1080p"]
    usd = per_sec * seconds
    if str(resolution).lower() == "4k":
        usd *= cfg["pricing_usd"]["video_4k_multiplier"]
    if audio:
        usd *= cfg["pricing_usd"]["video_audio_multiplier"]
    return round(usd, 4)


def est_text(cfg: dict, calls: int = 1) -> float:
    return round(cfg["pricing_usd"]["text_per_call"] * calls, 4)


def est_video_test(cfg: dict, calls: int = 1) -> float:
    return round(cfg["pricing_usd"]["video_test_per_call"] * calls, 4)


# ---------------------------------------------------------------- 台帳

def _month_of(ts: str) -> str:
    return ts[:7]  # ISO の YYYY-MM


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class Ledger:
    """usage.json の読み書きと月次集計。"""

    def __init__(self, cfg: dict, path: Path | None = None):
        self.cfg = cfg
        self.path = path or (state_dir(cfg) / USAGE_FILE)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                backup = self.path.with_suffix(".corrupt.json")
                self.path.rename(backup)
                print(f"[warn] 台帳が壊れていたため {backup.name} に退避しました")
        return {"entries": []}

    def _save(self) -> None:
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")

    # ---- 参照

    @property
    def entries(self) -> list:
        return self.data.get("entries", [])

    def month_key(self, ts: str | None = None) -> str:
        return _month_of(ts or _now_iso())

    def month_entries(self, month: str | None = None) -> list:
        m = month or self.month_key()
        return [e for e in self.entries if _month_of(e["ts"]) == m]

    def month_spend(self, month: str | None = None) -> float:
        return round(sum(e.get("est_usd", 0.0) for e in self.month_entries(month)), 4)

    def remaining(self, month: str | None = None) -> float:
        return round(self.cfg["monthly_budget_usd"] - self.month_spend(month), 4)

    def by_operation(self, month: str | None = None) -> dict:
        out: dict[str, float] = {}
        for e in self.month_entries(month):
            out[e["op"]] = round(out.get(e["op"], 0.0) + e.get("est_usd", 0.0), 4)
        return out

    # ---- 予算ガード

    def check(self, est_usd: float, what: str = "", force: bool = False) -> float:
        """呼び出し前の予算チェック。超過見込みなら BudgetError。"""
        remain = self.remaining()
        if force:
            return remain
        if est_usd > remain + 1e-9:
            raise BudgetError(
                f"月間予算を超えます: {what} 見積 ${est_usd:.2f} / 残り ${remain:.2f} "
                f"(予算 ${self.cfg['monthly_budget_usd']:.2f}, 今月消費 "
                f"${self.month_spend():.2f})\n"
                f"  → サイズ/秒数を下げる, 来月回し, または --force で強行")
        return remain

    # ---- 記録

    def record(self, *, op: str, model: str, est_usd: float,
               note: str = "", files: list | None = None, **extra) -> dict:
        entry = {"ts": _now_iso(), "op": op, "model": model,
                 "est_usd": round(est_usd, 4), "note": note,
                 "files": files or [], **extra}
        self.data.setdefault("entries", []).append(entry)
        self._save()
        return entry

    # ---- 表示

    def render_summary(self, month: str | None = None) -> str:
        m = month or self.month_key()
        spent = self.month_spend(m)
        budget = self.cfg["monthly_budget_usd"]
        remain = round(budget - spent, 4)
        lines = [
            f"月: {m}  予算 ${budget:.2f} / 消費 ${spent:.2f} / 残り ${remain:.2f}",
            "内訳:",
        ]
        by_op = self.by_operation(m)
        if not by_op:
            lines.append("  (記録なし)")
        for op, usd in sorted(by_op.items(), key=lambda kv: -kv[1]):
            n = len([e for e in self.month_entries(m) if e["op"] == op])
            lines.append(f"  {op:<12} ${usd:>6.2f}  ({n}回)")
        p = self.cfg["pricing_usd"]
        lines += [
            f"残りで実行可能 (目安単価):",
            f"  画像 1K ${p['image']['1K']:.2f}/枚 → 約{int(remain / p['image']['1K'])}枚",
            f"  画像 4K ${p['image']['4K']:.2f}/枚 → 約{int(remain / p['image']['4K'])}枚",
            f"  Veo 1080p ${p['video_per_second_1080p']:.2f}/秒 → 約{int(remain / p['video_per_second_1080p'])}秒",
        ]
        return "\n".join(lines)
