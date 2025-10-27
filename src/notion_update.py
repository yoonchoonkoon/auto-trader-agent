# notion_update.py
import os, csv, sys
from notion_client import Client
from dotenv import load_dotenv

# .env 파일을 상위 폴더에서 로드
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

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

def upsert_page(client, db_id, name, fast, slow, cagr, sharpe, maxdd):
    props = {
        "Name": {"title": [{"text": {"content": name}}]},
        "fast": {"number": fast},
        "slow": {"number": slow},
        "CAGR": {"number": cagr},
        "Sharpe(ann)": {"number": sharpe},
        "MaxDD": {"number": maxdd},
    }

    resp = client.search(
        query=name,
        filter={"property": "object", "value": "page"},
        page_size=10,
    )
    results = []

    for p in resp.get("results", []):
        if p.get("parent", {}).get("database_id") != db_id:
            continue
        title_rich = p.get("properties", {}).get("Name", {}).get("title", [])
        plain = "".join([t.get("plain_text", "") for t in title_rich]).strip()
        if plain == name:
            results.append(p)
    if results:
        page_id = results[0]["id"]
        client.pages.update(page_id=page_id, properties=props)
        print(f"[UPDATE] {name}")
    else:
        client.pages.create(parent={"database_id": db_id}, properties=props)
        print(f"[CREATE] {name}")

def to_notion(pages, client: Client):
    ok = 0
    for r in pages:
        title = f"fast{r['fast']}_slow{r['slow']}"
        upsert_page(
            client, NOTION_DB_ID,              # ✅ client를 첫 번째 인자로 추가
            title, r["fast"], r["slow"],
            r["CAGR"], r["Sharpe(ann)"], r["MaxDD"]
        )
        ok += 1              # ✅ 이 줄이 반드시 for 안쪽에 있어야 함
    print(f"[OK] Notion 업로드 완료: {ok} rows")

if __name__ == "__main__":
    ensure_env()
    client = Client(auth=NOTION_TOKEN)
    csv_path = os.path.join(os.path.dirname(__file__), "..", "reports", "grid_search_metrics.csv")
    pages = read_metrics(csv_path)
    to_notion(pages, client)
