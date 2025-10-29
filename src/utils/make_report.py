# src/utils/make_report.py
from __future__ import annotations
import os, pandas as pd
from datetime import datetime

SWEEP = "reports/sweep_summary.csv"
BEST  = "reports/best_sweep.csv"
OUT   = "reports/AutoTraderAgent_Day1_Report.md"

def md_table(df: pd.DataFrame, cols):
    df = df.loc[:, cols].copy()
    # 숫자 포맷
    if "final_equity" in df.columns:
        df["final_equity"] = df["final_equity"].map(lambda x: f"{x:.4f}")
    return df.to_markdown(index=False)

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    sweep = pd.read_csv(SWEEP, encoding="utf-8-sig")
    sweep["final_equity"] = pd.to_numeric(sweep["final_equity"], errors="coerce")
    sweep = sweep.sort_values(["final_equity","timestamp"], ascending=[False, False]).reset_index(drop=True)

    best = pd.read_csv(BEST, encoding="utf-8-sig")
    best_row = best.iloc[0].to_dict()

    top5 = sweep.head(5).copy()

    lines = []
    lines.append(f"# AI AutoTraderAgent – Day 1 Report")
    lines.append(f"_generated: {now}_\n")
    lines.append("## ✅ Best Strategy")
    lines.append(f"- **strategy**: `{best_row.get('strategy')}`")
    lines.append(f"- **final_equity**: **{best_row.get('final_equity'):.4f}**")
    lines.append(f"- **timestamp**: {best_row.get('timestamp')}")
    fig = best_row.get("figure_path")
    if isinstance(fig, str) and fig:
        lines.append(f"- **figure**: `{fig}`")
        # 이미지 경로가 상대경로면 그대로 표시
        lines.append(f"\n![equity]({fig})\n")
    else:
        lines.append("- figure: (not found in log)\n")

    lines.append("## 🏆 Top 5 (by final_equity)")
    lines.append(md_table(top5, ["strategy","final_equity","timestamp","fast","slow","fee_bp"]))
    lines.append("\n## 📂 Artifacts")
    lines.append("- `reports/best_sweep.csv`")
    lines.append("- `reports/sweep_summary.csv`")
    lines.append("- `reports/figures/` (all PNGs)")
    content = "\n".join(lines)

    with open(OUT, "w", encoding="utf-8-sig") as f:
        f.write(content)
    print(f"✅ report saved → {OUT}")

if __name__ == "__main__":
    main()