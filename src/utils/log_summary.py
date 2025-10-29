# src/utils/log_summary.py
from __future__ import annotations
import re, os, pandas as pd
from datetime import datetime
from glob import glob

def parse_run_log(path: str):
    """run_YYYY-MM-DD_HH-MM.log 파일에서 전략명과 최종 수익 추출"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.findall(r"\[OK\]\s+(\S+).*?final_equity=([\d\.]+)", text)
    rows = []
    for name, eq in m:
        ts = re.search(r"run_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2})", os.path.basename(path))
        rows.append({
            "log_file": os.path.basename(path),
            "strategy": name,
            "final_equity": float(eq),
            "timestamp": ts.group(1) if ts else None
        })
    return rows

def summarize_logs(log_dir="reports/logs", out_csv="reports/summary_log.csv"):
    files = sorted(glob(os.path.join(log_dir, "run_*.log")))
    all_rows = []
    for fpath in files:
        all_rows.extend(parse_run_log(fpath))
    if not all_rows:
        print("⚠️ no log data found.")
        return None
    df = pd.DataFrame(all_rows)
    df = df.sort_values("timestamp").reset_index(drop=True)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"✅ summary saved → {out_csv} ({len(df)} rows)")
    return df

if __name__ == "__main__":
    summarize_logs()