# src/sweep_runner.py
from __future__ import annotations
import itertools, yaml, datetime, os, pathlib, subprocess
import sys

def run_one(cfg_path: str, name: str, fast: int, slow: int, fee_bp: float):
    """개별 조합 실행용 설정 임시파일 생성 후 strategy_engine 실행"""
    tmp_name = f"config/tmp_{name}.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        base = yaml.safe_load(f)

    # 기존 필드 복제 후 수정
    base["strategies"] = [{
        "name": name,
        "fast": fast,
        "slow": slow,
        "fee_bp": fee_bp
    }]

    # 임시 config 생성
    with open(tmp_name, "w", encoding="utf-8") as f:
        yaml.dump(base, f, allow_unicode=True)

    # 실제 실행
    print(f"▶ {name}: fast={fast}, slow={slow}, fee={fee_bp}")
    subprocess.run([sys.executable, "-m", "src.strategy_engine", tmp_name], check=False)

def sweep(cfg_path="config/sweep.yaml"):
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    grid = cfg.get("grid", {})
    fasts = grid.get("fast", [5])
    slows = grid.get("slow", [50])
    fees  = grid.get("fee_bp", [0])

    prefix = cfg.get("name_prefix", "sweep")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    report_dir = cfg.get("report_dir", "reports")
    pathlib.Path(report_dir).mkdir(exist_ok=True)

    combos = list(itertools.product(fasts, slows, fees))
    print(f"🔁 총 {len(combos)} 조합 실행 시작")

    for fast, slow, fee in combos:
        name = f"{prefix}_f{fast}_s{slow}_fee{fee}_{ts}"
        run_one(cfg_path, name, fast, slow, fee)

if __name__ == "__main__":
    sweep()