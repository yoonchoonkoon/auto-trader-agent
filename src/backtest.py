import pandas as pd

def run(prices: pd.Series, positions: pd.Series, fee_bp: float = 5.0):
    """
    prices: 종가 시계열
    positions: 1=long, 0=flat (시그널)
    fee_bp: 거래비용(bps), 기본 5bp=0.05%
    """
    ret = prices.pct_change().fillna(0.0)
    pos = positions.shift(1).fillna(0)               # 체결 지연 1틱
    gross = pos * ret
    turn = pos.diff().abs().fillna(0)               # 거래회전
    fee = turn * (fee_bp / 10000.0)
    pnl = (gross - fee).rename("pnl")
    equity = (1 + pnl).cumprod().rename("equity")

    # 통계치
    if len(equity) > 0:
        ann = 252
        cagr = (equity.iloc[-1] ** (ann / max(len(equity), 1)) - 1) if equity.iloc[-1] > 0 else 0.0
        sharpe = (pnl.mean() / pnl.std() * (ann ** 0.5)) if pnl.std() > 0 else 0.0
        mdd = (equity / equity.cummax() - 1).min()
    else:
        cagr = sharpe = 0.0
        mdd = 0.0

    stats = {"CAGR": float(cagr), "Sharpe(ann)": float(sharpe), "MaxDD": float(mdd)}
    return pnl, equity, stats
