from data_loader import load_prices
from strategy import simple_ma
from backtest import run
import os

if __name__ == "__main__":
    df = load_prices("../data/sample_prices.csv")  # date, close 컬럼
    signal = simple_ma(df["close"])
    pnl, equity, stats = run(df["close"], signal)
    print(stats)
    
from visualize import plot_equity_curve

reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
out_png = os.path.join(reports_dir, "equity_curve.png")

plot_equity_curve(df, out_png, title="Equity Curve – AutoTraderAgent")
