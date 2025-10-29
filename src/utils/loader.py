# src/utils/loader.py
from __future__ import annotations
import pandas as pd

def load_prices(csv_path: str) -> pd.DataFrame:
    """
    CSV 컬럼 요구사항: date, close
    - date: 파싱하여 datetime
    - close: 숫자형으로 보정
    반환: 날짜 오름차순 정렬된 DataFrame
    """
    df = pd.read_csv(csv_path)
    required = {"date", "close"}
    missing = required - set(map(str.lower, df.columns))
    if missing:
        raise ValueError(f"CSV에 필요한 컬럼 누락: {missing} (필수: {required})")

    # 컬럼 명 소문자 통일(혼용 방지)
    df.columns = [c.lower() for c in df.columns]

    # 타입 정리
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")

    # 결측/비정상 제거
    df = df.dropna(subset=["close"]).copy()

    # 정렬 및 인덱스 초기화
    df = df.sort_values("date").reset_index(drop=True)
    return df