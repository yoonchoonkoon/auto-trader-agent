# src/optimizer.py
from __future__ import annotations
import itertools
import pandas as pd
import numpy as np
from data_loader import load_prices
from backtest import run

def generate_signal_ma(close: pd.Series, fast: int, slow: int) -> pd.Series:
    """단순 이동평균 크로스오버 포지션(-1/1) 생성"""
    fast_ma = close.rolling(fast).mean()
    slow_ma = close.rolling(slow).mean()
    pos = np.where(fast_ma > slow_ma, 1, -1)  # fast>slow이면 매수, 아니면 매도
    pos = pd.Series(pos, index=close.index).shift(1).fillna(0)  # 다음날 체결
    return pos

def grid_search_ma(close: pd.Series,
                   fast_list=(5, 10, 20),
                   slow_list=(50, 100, 200)) -> pd.DataFrame:
    """fast<slow 조합만 탐색, 성능표 반환"""
    rows = []
    for f, s in itertools.product(fast_list, slow_list):
        if f >= s:  # 비합리 조합 스킵
            continue
        signal = generate_signal_ma(close, f, s)
        pnl, equity, stats = run(close, signal)  # 기존 run 재사용
        rows.append({
            "fast": f,
            "slow": s,
            "CAGR": stats.get("CAGR"),
            "Sharpe(ann)": stats.get("Sharpe(ann)"),
            "MaxDD": stats.get("MaxDD"),
        })
    df = pd.DataFrame(rows)
    return df.sort_values(["Sharpe(ann)", "CAGR"], ascending=[False, False]).reset_index(drop=True)

if __name__ == "__main__":
    import numpy as np
    import pandas as pd

    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(300))  # 가짜 주가 300일
    df = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=300),
                       "close": prices})
    results = grid_search_ma(df["close"], fast_list=(3,5,10), slow_list=(15,30,60))
    print(results.head(10))

    import os
    
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    out_csv = os.path.join(reports_dir, "ma_grid_results.csv")
    results.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[OK] Saved: {os.path.abspath(out_csv)}")

best = results.iloc[0]
print(f"[BEST] fast={int(best.fast)}, slow={int(best.slow)}  Sharpe={best['Sharpe(ann)']:.3f}  CAGR={best['CAGR']:.3f}")

# === 57~66줄 추가 ===
from visualize import plot_equity_curve

best_f, best_s = int(best.fast), int(best.slow)
signal_best = generate_signal_ma(df["close"], best_f, best_s)
pnl, equity, stats = run(df["close"], signal_best)

viz_df = pd.DataFrame({"date": df["date"], "equity": equity})
import os
reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(reports_dir, exist_ok=True)
out_png = os.path.join(reports_dir, f"equity_best_f{best_f}_s{best_s}.png")
plot_equity_curve(viz_df, out_png, title=f"Equity Curve - fast={best_f}, slow={best_s}")
print(f"[OK] Saved equity: {os.path.abspath(out_png)}")