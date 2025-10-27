# check_db_titles.py
from notion_client import Client
from dotenv import load_dotenv
import os, sys

ENV_PATH = r"C:\projects\auto-trader-agent\.env"  # 고정 경로
ok = load_dotenv(dotenv_path=ENV_PATH, override=True)
if not ok:
    print(f"❌ .env 로드 실패: {ENV_PATH}")
    sys.exit(1)

TOKEN = os.getenv("NOTION_TOKEN")
MID   = os.getenv("NOTION_DB_ID")          # Metrics
AID   = os.getenv("NOTION_ALERT_DB_ID")    # Alerts

def die(msg): print(msg); sys.exit(2)
if not TOKEN: die("❌ NOTION_TOKEN 비어있음")
if not MID:   die("❌ NOTION_DB_ID 비어있음 (Metrics)")
if not AID:   die("❌ NOTION_ALERT_DB_ID 비어있음 (Alerts)")

n = Client(auth=TOKEN)

def db_title(db_id: str) -> str:
    meta = n.databases.retrieve(database_id=db_id)
    return "".join(t.get("plain_text","") for t in meta.get("title", [])).strip()

try:
    mt = db_title(MID)
    at = db_title(AID)
except Exception as e:
    print("❌ API 호출 에러:", repr(e))
    print("   - Notion 페이지에서 Alerts/Metrics 둘 다 'Add connections'로 Integration 연결 필요")
    sys.exit(3)

print("=== DB 확인 결과 ===")
print(f"[Metrics] ID={MID} | Title='{mt}'")
print(f"[Alerts ] ID={AID} | Title='{at}'")

if MID == AID:
    die("❌ 두 DB ID가 같습니다. .env 분리 필요")
elif mt == at:
    print("⚠️ 두 DB 제목이 동일합니다. 제목을 다르게 권장")
else:
    print("✅ OK: ID/제목 모두 구분됨 (완전 분리)")