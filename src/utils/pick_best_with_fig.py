# src/utils/pick_best_with_fig.py
from __future__ import annotations
import os, re, pandas as pd

SWEEP_CSV = "reports/sweep_summary.csv"
LOG_DIR   = "reports/logs"
OUT_CSV   = "reports/best_sweep.csv"

FIG_RE = re.compile(r"fig=([^\s]+\.png)")

def extract_fig_path(log_path: str, strategy_name: str) -> str | None:
    """해당 run 로그에서 특정 전략명 줄의 fig=...png 경로 추출"""
    if not os.path.exists(log_path):
        return None
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            if strategy_name in line and "fig=" in line:
                m = FIG_RE.search(line)
                if m:
                    # 역슬래시는 그대로 두어도 Windows에서 정상
                    return m.group(1)
    return None

def pick_best_with_fig(sweep_csv: str = SWEEP_CSV, out_csv: str = OUT_CSV):
    if not os.path.exists(sweep_csv):
        print(f"⚠️ not found: {sweep_csv}")
        return None

    df = pd.read_csv(sweep_csv, encoding="utf-8-sig")
    df["final_equity"] = pd.to_numeric(df["final_equity"], errors="coerce")
    # 성과 내림차순 → 최신 우선
    df = df.sort_values(["final_equity","timestamp"], ascending=[False, False]).reset_index(drop=True)

    best = df.iloc[[0]].copy()
    log_file = best.loc[0, "log_file"]
    strat    = best.loc[0, "strategy"]

    log_path = os.path.join(LOG_DIR, log_file)
    fig_path = extract_fig_path(log_path, strat)
    best["figure_path"] = fig_path

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    best.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print("✅ Best sweep saved →", out_csv)
    print(best.to_string(index=False))
    if not fig_path:
        print("ℹ️ figure_path not found in log. (전략명이 로그와 다르거나 로그 형식이 다를 수 있음)")
    return best

if __name__ == "__main__":
    pick_best_with_fig()