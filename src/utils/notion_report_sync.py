# src/utils/notion_report_sync.py  (create-only, super simple)
from pathlib import Path
import csv, os
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
BEST = ROOT / "reports" / "best_sweep.csv"

def env_or_fail(k):
    v = os.getenv(k)
    if not v:
        raise RuntimeError(f"{k} 누락")
    return v

def to_number(x):
    try:
        return float(x)
    except Exception:
        return None

def main():
    load_dotenv()
    token = env_or_fail("NOTION_TOKEN")
    db_id = env_or_fail("NOTION_DB_ID")
    notion = Client(auth=token)

    if not BEST.exists():
        print(f"파일 없음: {BEST}")
        return

    with BEST.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            date_str = datetime.now().strftime("%Y-%m-%d")
            strategy = row.get("strategy") or "SMA_cross"
            fast = int(float(row.get("fast", 0)))
            slow = int(float(row.get("slow", 0)))
            fee = to_number(row.get("fee"))
            final_equity = to_number(row.get("final_equity"))
            figure_path = row.get("figure_path") or ""
            report_path = row.get("report_path") or ""
            commit_hash = row.get("commit_hash") or ""

            props = {
              "Date": {"date": {"start": date_str}},
              "StrategyName": {"title": [{"text": {"content": strategy}}]},
              "Fast": {"number": fast},
              "Slow": {"number": slow},
              "Fee": {"number": fee},
              "FinalEquity": {"number": final_equity},
              "FigurePath": {"url": figure_path or None},
              "ReportPath": {"url": report_path or None},
              "CommitHash": {"rich_text": [{"text": {"content": commit_hash}}]},
              "Notes": {"rich_text": [{"text": {"content": f'{date_str}-{strategy}-{fast}-{slow}-{fee}'}}]},
            }
            notion.pages.create(parent={"database_id": db_id}, properties=props)
            print(f"[CREATED] {strategy} f{fast}s{slow} fee{fee}")

if __name__ == "__main__":
    main()