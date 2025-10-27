# src/visualize.py
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

def ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

def _pick_equity_series(df: pd.DataFrame) -> pd.Series:
    if 'equity' in df.columns:
        return df['equity'].astype(float)
    elif 'cum_pnl' in df.columns:
        return 1.0 + df['cum_pnl'].astype(float)
    elif 'return' in df.columns:
        return (1.0 + df['return'].astype(float)).cumprod()
    elif 'close' in df.columns:
        return df['close'] / df['close'].iloc[0]
    else:
        return pd.Series(range(1, len(df) + 1), index=df.index) / len(df)

def plot_equity_curve(df: pd.DataFrame, out_png: str, title: str = "Equity Curve"):
    ensure_dir(out_png)
    equity = _pick_equity_series(df)
    x = df.get('date', df.index)
    plt.figure(figsize=(10, 5))
    plt.plot(x, equity, linewidth=1.5)
    plt.title(title)
    plt.xlabel("Date" if 'date' in df.columns else "Index")
    plt.ylabel("Equity (normalized)")
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"[OK] 그래프 저장 완료: {out_png}")
