# src/utils/summary_merge.py
from __future__ import annotations
import re, os, pandas as pd

IN_CSV  = "reports/summary_log.csv"
OUT_CSV = "reports/sweep_summary.csv"

# 두 형식 모두 지원:
# 1) sweep_f2_s10_fee5_20251029_1644
# 2) fast2_slow5  (fee 없음)
PAT_SWEEP = re.compile(r"f(?P<fast>\d+)_s(?P<slow>\d+)_fee(?P<fee>\d+)")
PAT_SIMPLE = re.compile(r"fast(?P<fast>\d+)_slow(?P<slow>\d+)")

def parse_params(name: str):
    m = PAT_SWEEP.search(name)
    if m:
        return int(m["fast"]), int(m["slow"]), int(m["fee"])
    m = PAT_SIMPLE.search(name)
    if m:
        return int(m["fast"]), int(m["slow"]), None
    return None, None, None

def build_sweep_summary(in_csv: str = IN_CSV, out_csv: str = OUT_CSV):
    if not os.path.exists(in_csv):
        print(f"⚠️ not found: {in_csv}")
        return None
    df = pd.read_csv(in_csv, encoding="utf-8-sig")
    df["final_equity"] = pd.to_numeric(df["final_equity"], errors="coerce")

    fast, slow, fee = zip(*df["strategy"].apply(parse_params))
    df["fast"], df["slow"], df["fee_bp"] = fast, slow, fee

    df = df.sort_values(by=["final_equity","timestamp"], ascending=[False, False]).reset_index(drop=True)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"✅ sweep summary saved → {out_csv} ({len(df)} rows)")
    print(df.head(5).to_string(index=False))
    return df

if __name__ == "__main__":
    build_sweep_summary()