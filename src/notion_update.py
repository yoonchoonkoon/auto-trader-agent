# notion_update.py
import os, csv, sys
from notion_client import Client

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")  # Notion Integration secret
NOTION_DB_ID = os.environ.get("NOTION_DB_ID")  # 대상 DB ID

def ensure_env():
    if not NOTION_TOKEN or not NOTION_DB_ID:
        print("[ERR] 환경변수 NOTION_TOKEN / NOTION_DB_ID 가 필요합니다.")
        print("      PowerShell 예) $env:NOTION_TOKEN='secret_xxx'; $env:NOTION_DB_ID='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'")
        sys.exit(1)

def read_metrics(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f)):
            try:
                rows.append({
                    "fast": int(row["fast"]),
                    "slow": int(row["slow"]),
                    "CAGR": float(row["CAGR"]),
                    "Sharpe(ann)": float(row["Sharpe(ann)"]),
                    "MaxDD": float(row["MaxDD"]),
                })
            except Exception as e:
                print(f"[WARN] {i}행 스킵: {e}")
    return rows

def to_notion(pages, client: Client):
    ok = 0
    for r in pages:
        title = f"fast{r['fast']}_slow{r['slow']}"
        client.pages.create(
            parent={"database_id": NOTION_DB_ID},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "fast": {"number": r["fast"]},
                "slow": {"number": r["slow"]},
                "CAGR": {"number": r["CAGR"]},
                "Sharpe(ann)": {"number": r["Sharpe(ann)"]},
                "MaxDD": {"number": r["MaxDD"]},
            },
        )
        ok += 1
    print(f"[OK] Notion 업로드 완료: {ok} rows")

if __name__ == "__main__":
    ensure_env()
    client = Client(auth=NOTION_TOKEN)
    csv_path = os.path.join(os.path.dirname(__file__), "..", "reports", "grid_search_metrics.csv")
    pages = read_metrics(csv_path)
    to_notion(pages, client)
