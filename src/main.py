from data_loader import load_prices
from strategy import simple_ma
from backtest import run
from visualize import compare_equity_curves
import os
import pandas as pd

FAST_WINDOWS = [5, 10, 20]
SLOW_WINDOWS = [50, 100, 200]

if __name__ == "__main__":
    df = load_prices("data/sample_prices.csv")
    signal = simple_ma(df["close"])
    pnl, equity, stats = run(df["close"], signal)
    print(stats)    

    results = {}
    rows = []
    for fast in FAST_WINDOWS:
        for slow in SLOW_WINDOWS:
            label = f"fast{fast}_slow{slow}"
            signal = simple_ma(df["close"], fast, slow)
            pnl, equity, stats = run(df["close"], signal)
            results[label] = equity
            rows.append({"fast": fast, "slow": slow,
                "CAGR": stats["CAGR"],
                "Sharpe(ann)": stats["Sharpe(ann)"],
                "MaxDD": stats["MaxDD"]
            })

    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    df_metrics = pd.DataFrame(rows)
    metrics_csv = os.path.join(reports_dir, "grid_search_metrics.csv")
    df_metrics.to_csv(metrics_csv, index=False, encoding="utf-8-sig")
    print("[OK] 메트릭 저장:", metrics_csv)

from visualize import compare_equity_curves
compare_equity_curves(results, "reports/compare_equity_curves.png")

    # === Docsify Report Auto-Update ===
with open(os.path.join(reports_dir, "README.md"), "w", encoding="utf-8") as f:
    f.write("# 📊 Auto-Trader-Agent 보고서\n\n")
    f.write("## 📈 전략 비교 그래프\n\n")
    f.write("![equity](compare_equity_curves.png)\n\n")
    f.write("## 📋 Grid Search Metrics\n\n")
    f.write("| fast | slow | CAGR | Sharpe(ann) | MaxDD |\n")
    f.write("|---|---|---|---|---|\n")
    for r in rows:
        f.write(f"| {r['fast']} | {r['slow']} | {r['CAGR']:.3f} | {r['Sharpe(ann)']:.3f} | {r['MaxDD']:.3f} |\n")
print("[OK] Docsify 보고서 업데이트: reports/README.md")
