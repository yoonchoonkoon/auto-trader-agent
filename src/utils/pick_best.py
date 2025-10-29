# src/utils/pick_best.py
from __future__ import annotations
import os
import pandas as pd

def pick_best(summary_csv="reports/summary_log.csv",
              out_csv="reports/best_run.csv"):
    if not os.path.exists(summary_csv):
        print(f"⚠️ not found: {summary_csv}")
        return None

    # UTF-8 BOM 대응
    df = pd.read_csv(summary_csv, encoding="utf-8-sig")
    if df.empty:
        print("⚠️ summary is empty.")
        return None

    # 타입 보정
    df["final_equity"] = pd.to_numeric(df["final_equity"], errors="coerce")
    # 동률이면 최신 timestamp 우선
    df_sorted = df.sort_values(
        by=["final_equity", "timestamp"],
        ascending=[False, False]
    ).reset_index(drop=True)

    best = df_sorted.iloc[[0]]
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    best.to_csv(out_csv, index=False, encoding="utf-8-sig")

    row = best.iloc[0].to_dict()
    print(f"✅ best saved → {out_csv}")
    print(f"   strategy={row.get('strategy')}, final_equity={row.get('final_equity')}, ts={row.get('timestamp')}")
    return best

if __name__ == "__main__":
    pick_best()