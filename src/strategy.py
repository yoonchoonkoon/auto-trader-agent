import pandas as pd

def simple_ma(prices: pd.Series, fast=2, slow=3) -> pd.Series:
    """fast/slow 이동평균 골든크로스 -> 1(진입), 데드크로스 -> 0(청산)"""
    ma_fast = prices.rolling(fast).mean()
    ma_slow = prices.rolling(slow).mean()
    signal = (ma_fast > ma_slow).astype(int)  # 1=long, 0=flat
    return signal
