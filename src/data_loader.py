import pandas as pd

def load_prices(path: str) -> pd.DataFrame:
    """CSV 파일에서 시계열 데이터 불러오기"""
    df = pd.read_csv(path, parse_dates=['date'])
    df = df.set_index('date').sort_index()
    return df
