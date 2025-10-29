# src/strategies/ma_crossover.py
from __future__ import annotations
import pandas as pd

def ma_crossover(df: pd.DataFrame, fast: int, slow: int, fee_bp: float = 0.0) -> pd.DataFrame:
    """
    단순 이동평균(MA) 크로스 전략
    - fast, slow: 이동평균 기간
    - fee_bp: 체결 시 비용(베이시스 포인트, 1bp = 0.01%). 예: 10 → 0.10%
    가정:
      * 시그널은 오늘 계산되어 '다음 거래일'에 진입/청산(pos를 1칸 시프트)
      * 자산 수익률은 close 기준 일별 수익률
    반환: 입력 df에 전략 컬럼을 추가한 DataFrame
    컬럼:
      ma_fast, ma_slow, signal(1/0), pos, ret, trade, fee, strat, equity
    """
    out = df.copy()

    # 필수 컬럼 확인
    cols = {c.lower() for c in out.columns}
    if not {"date", "close"}.issubset(cols):
        raise ValueError("필수 컬럼(date, close)이 필요합니다.")

    # MA 계산
    out["ma_fast"] = out["close"].rolling(int(fast)).mean()
    out["ma_slow"] = out["close"].rolling(int(slow)).mean()

    # 시그널: 빠른선이 느린선을 상회하면 1(롱), 아니면 0(현금)
    out["signal"] = (out["ma_fast"] > out["ma_slow"]).astype(int)

    # 포지션: 다음날 체결 가정
    out["pos"] = out["signal"].shift(1).fillna(0)

    # 기본 자산 수익률
    out["ret"] = out["close"].pct_change().fillna(0)

    # 체결 이벤트 (포지션 변경일)
    out["trade"] = out["pos"].diff().abs().fillna(out["pos"]).astype(int)

    # 거래비용(bp → 비율)
    fee_rate = fee_bp / 10000.0
    out["fee"] = (-fee_rate) * out["trade"]

    # 전략 일수익률 = 포지션 * 기초수익률 + 비용
    out["strat"] = out["pos"] * out["ret"] + out["fee"]

    # 누적자산(전략 에퀴티)
    out["equity"] = (1 + out["strat"]).cumprod()

    return out