from notion_client.errors import APIResponseError
from notion_client import Client
from dotenv import load_dotenv
import os, re, glob, datetime, sys
from pathlib import Path
from datetime import datetime

# ========================================================
# 1. DB 메타 정보 조회 및 스키마 자동 보강
# ========================================================
def get_database_meta(notion, db_id: str):
"""
1) 현재 db_id 메타를 조회.
2) properties가 있으면 그대로 반환.
3) data_sources가 있어도, 404/권한오류면 무시하고 현 메타 반환.
"""
meta = notion.databases.retrieve(database_id=db_id)
if "properties" in meta:
    return meta

for s in meta.get("data_sources") or []:
    source_id = s.get("database_id") or s.get("id")
    if not source_id or source_id == db_id:
        continue
    try:
        src = notion.databases.retrieve(database_id=source_id)
        if "properties" in src:
            return src
    except APIResponseError as e:
        print(f"⚠️ Linked source {source_id} ignored ({e}).")
        continue
return meta

def ensure_alerts_schema(notion, db_id, db_meta):
props = db_meta.get("properties", {})
needed = {
    "Summary":   {"rich_text": {}},
    "Started":   {"date": {}},
    "Ended":     {"date": {}},
    "Timestamp": {"date": {}},
    "Host":      {"rich_text": {}},
}
missing = {k:v for k,v in needed.items() if k not in props}
if not missing:
    return db_meta

notion.databases.update(database_id=db_id, properties=missing)
return notion.databases.retrieve(database_id=db_id)

# ========================================================
# 2. 로그 탐색 및 파싱
# ========================================================
FAIL_MARKERS = [">>> Job FAILED", "Traceback (most recent call last):"]
SUCCESS_MARKER = ">>> Job SUCCEEDED"

def find_latest_log(log_dir: str) -> str:
files = glob.glob(os.path.join(log_dir, "notion_sync_*.log"))
if not files:
    return ""
return max(files, key=os.path.getmtime)

def parse_log(filepath: str):
if not filepath or not os.path.exists(filepath):
    return {"status": "NO_LOG", "summary": "로그 없음", "detail": ""}
with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

status = ("SUCCESS" if SUCCESS_MARKER in content else
            "FAILED" if any(m in content for m in FAIL_MARKERS) else "UNKNOWN")
tail = "\n".join(content.splitlines()[-60:])
err_lines = [line for line in tail.splitlines() if any(x in line for x in ["ERROR", "Traceback", "FAILED"])]
summary = "\n".join(err_lines)[:400] if err_lines else ("성공" if status=="SUCCESS" else "확인필요")

start_match = re.search(r">>> Starting .* at (.+)", content)
end_match   = re.search(r">>> Job (?:SUCCEEDED|FAILED) at (.+)", content)
started_at  = start_match.group(1) if start_match else None
ended_at    = end_match.group(1)   if end_match   else None

return {"status": status, "summary": summary, "detail": tail,
        "started_at": started_at, "ended_at": ended_at}

# ========================================================
# 3. Alerts DB에 기록
# ========================================================
SCRIPT_MODE = "alerts"  # notion_update.py는 "metrics"로 지정

def guard_wrong_db(notion: Client, target_db_id: str):
meta = notion.databases.retrieve(database_id=target_db_id)
title = "".join(t.get("plain_text", "") for t in meta.get("title", [])).lower()
if SCRIPT_MODE == "alerts" and "metrics" in title:
    print("Safety stop: Alerts 스크립트가 Metrics DB에 접근 시도. 중단.")
    raise SystemExit(3)
if SCRIPT_MODE == "metrics" and "alerts" in title:
    print("Safety stop: Metrics 스크립트가 Alerts DB에 접근 시도. 중단.")
    raise SystemExit(3)

def _detect_title_prop(props_info: dict) -> str:
for k, v in props_info.items():
    if v.get("type") == "title":
        return k
return "Name"

def get_alerts_db_meta(notion, db_id):
"""
Alerts DB의 메타정보(properties)를 안전하게 로드하는 함수.
1차 조회 후 필수 속성 누락 시 1회 재조회하고,
그래도 없으면 RuntimeError 발생.
"""
meta = notion.databases.retrieve(db_id)
props = meta.get("properties", {})

required = ["Summary", "Started", "Ended", "Timestamp", "Host"]
missing = [k for k in required if k not in props]

# 1회 재조회 로직 (Notion 캐시 반영 지연 대응)
if missing:
    meta = notion.databases.retrieve(db_id)
    props = meta.get("properties", {})
    missing = [k for k in required if k not in props]
    if missing:
        raise RuntimeError(f"[ERROR] Alerts DB properties missing: {missing}")

print(f"[OK] Alerts DB meta loaded: {list(props.keys())[:6]}")
return props

def push_notion(parsed: dict) -> int:
from dotenv import load_dotenv
from notion_client import Client
import os, datetime

print("🔍 [DEBUG] push_notion() 시작")

dotenv_path = Path.cwd() / ".env"
load_dotenv(dotenv_path=str(dotenv_path))
token = os.getenv("NOTION_TOKEN")
db_id = os.getenv("NOTION_ALERT_DB_ID")

if not token or not db_id:
    print("❌ [DEBUG] 환경변수 누락 (NOTION_TOKEN 또는 NOTION_ALERT_DB_ID 없음)")
    return 2

notion = Client(auth=token, notion_version="2022-06-28")
print("✅ [DEBUG] Notion Client 연결 성공")

try:
    db_meta = get_database_meta(notion, db_id)
    db_meta = ensure_alerts_schema(notion, db_id, db_meta)
    props_info = db_meta["properties"]
    title_prop = _detect_title_prop(props_info)
    print("✅ [DEBUG] DB 메타 정보 확인 완료")

except Exception as e:
    print(f"⚠️ [DEBUG] DB 메타 불러오기 실패 → {e}")
    props_info = None
    title_prop = None

now = datetime.datetime.now()
status = parsed.get("status", "UNKNOWN")
summary = parsed.get("summary") or parsed.get("detail", "")[:200]
started = parsed.get("started_at")
ended = parsed.get("ended_at")
host = os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "unknown-host"

def _to_iso(s):
if not s:
    return None

# ✅ tz(+09:00) 포함된 ISO 문자열은 그대로 반환
try:
    return datetime.datetime.fromisoformat(s).isoformat()
except Exception:
    pass

# ✅ 포맷 변환 분기
try:
        return datetime.datetime.strptime(s, "%m/%d/%Y %H:%M:%S").isoformat()
except Exception:
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").isoformat()
    except Exception:
        return None
        
from datetime import timezone
now_local = datetime.datetime.now().astimezone()  # 현재 시스템의 지역 시간대 포함
started = parsed.get("started_at") or now_local.isoformat(timespec="seconds")
ended   = parsed.get("ended_at")   or now_local.isoformat(timespec="seconds")
stamp   = now_local.isoformat(timespec="seconds")

# 정상 경로
print(f"[DEBUG] times -> started={started} | ended={ended} | stamp={stamp}")
if props_info and title_prop:
    print("🟢 [DEBUG] 정상 경로로 알림 전송 시도")
    properties = {
        title_prop: {"title": [{"text": {"content": f"[{status}] Notion Sync"}}]},
        "Summary": {"rich_text": [{"text": {"content": summary or ""}}]},
        "Started": {"date": {"start": _to_iso(started)}} if started else None,
        "Ended": {"date": {"start": _to_iso(ended)}} if ended else None,
        "Timestamp": {"date": {"start": now.isoformat()}},
        "Host": {"rich_text": [{"text": {"content": host}}]},
    }

    properties = {k: v for k, v in properties.items() if v is not None}
    page = notion.pages.create(parent={"database_id": db_id}, properties=properties)
    print(f"✅ [OK] Alerts row inserted -> {page.get('url')}")
    return 0

# -------------------------------
# 예비(우회) 경로
# -------------------------------
else:
    print("⚠️ [DEBUG] 우회 경로 진입 — props_info/title_prop 없음")
    title_candidates = ["이름", "Name"]
    last_err = None
    for tp in title_candidates:
        try:
            page = notion.pages.create(
                parent={"database_id": db_id},
                properties={tp: {"title": [{"text": {"content": f"[{status}] Notion Sync (fallback)"}}]}},
            )
            print(f"✅ [OK] Fallback으로 row 추가 성공 (컬럼={tp})")
            return 0
        except Exception as e:
            last_err = e
            print(f"❌ [DEBUG] Fallback 실패 ({tp}) → {e}")
            continue

    print("❌ [DEBUG] 모든 Fallback 실패 — 'Name' 또는 '이름' 컬럼이 없을 수 있음")
    if last_err:
        print("   마지막 오류:", repr(last_err))
    return 2

# ============================================================
# 4. 엔트리포인트
# ============================================================
def main():
print("🔍 [DEBUG] main() start")
from dotenv import load_dotenv
load_dotenv()

log_dir = os.path.join("reports", "logs")
print(f"🔍 [DEBUG] log_dir = {os.path.abspath(log_dir)}")

latest = find_latest_log(log_dir)
print(f"🔍 [DEBUG] latest log = {latest!r}")

if not latest:
    parsed = {
        "status": "UNKNOWN",
        "summary": "no log",
        "detail": "",
        "started_at": None,
        "ended_at": None
    }
else:
    parsed = parse_log(latest)

print(f"🔍 [DEBUG] parsed.status={parsed.get('status')}, "
        f"started={parsed.get('started_at')}, ended={parsed.get('ended_at')}")
rc = push_notion(parsed)
print(f"✅ [DEBUG] push_notion() returned rc={rc}")
return rc

if __name__ == "__main__":
rc = push_notion({
    "status": "SUCCESS",
    "summary": "smoke test",
    "detail": "pipeline ok",
    "started_at": datetime.now().isoformat(timespec="seconds"),
    "ended_at":   datetime.now().isoformat(timespec="seconds"),
})
print("RETURN CODE:", rc)