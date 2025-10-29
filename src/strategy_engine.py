# src/strategy_engine.py
from __future__ import annotations
import os, datetime, pathlib, yaml
import matplotlib.pyplot as plt
import sys

from src.utils.loader import load_prices
from src.strategies.ma_crossover import ma_crossover

def run(config_path="config/config.yaml"):
    # --- 설정 읽기 ---
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    data_path   = cfg["data_path"]
    report_dir  = cfg.get("report_dir", "reports")
    fig_dir     = cfg.get("figure_dir", f"{report_dir}/figures")
    log_dir     = cfg.get("log_dir", f"{report_dir}/logs")
    pathlib.Path(fig_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(log_dir).mkdir(parents=True, exist_ok=True)

    # --- 로그 시작 ---
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    log_path = os.path.join(log_dir, f"run_{ts}.log")
    with open(log_path, "a", encoding="utf-8") as fp:
        fp.write(f">>> Run started at {ts}\n")

    # --- 데이터 로드 ---
    df = load_prices(data_path)

    # --- 전략 실행 루프 ---
    for s in cfg.get("strategies", []):
        name   = s["name"]
        fast   = int(s["fast"])
        slow   = int(s["slow"])
        fee_bp = float(s.get("fee_bp", 0.0))

        res = ma_crossover(df, fast, slow, fee_bp=fee_bp)

        # 그림 저장
        ax = res.plot(x="date", y="equity", title=f"{name} (fast={fast}, slow={slow}, fee_bp={fee_bp})")
        fig = ax.get_figure()
        out_png = os.path.join(fig_dir, f"{name}_{ts}.png")
        fig.savefig(out_png, dpi=140)
        plt.close(fig)

        # 로그
        with open(log_path, "a", encoding="utf-8") as fp:
            last_eq = float(res["equity"].iloc[-1])
            fp.write(f"[OK] {name} → final_equity={last_eq:.4f}, fig={out_png}\n")

if __name__ == "__main__":
    cfg = sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml"
    run(cfg)