# src/utils/notion_alert.py
import os, socket
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client

# ★ 당신 Alert DB 실제 컬럼명으로 필요시 바꾸세요
PROP = {
    "TITLE": "이름",         # Title(제목) 필드의 표시이름
    "SUMMARY": "Summary",    # Rich text
    "STATUS": "Status",      # Select (SUCCESS/FAILED/RUNNING)
    "STARTED": "Started",    # Date/Time
    "ENDED": "Ended",        # Date/Time
    "TIMESTAMP": "Timestamp",# Date/Time
    "HOST": "Host",          # Rich text or Text
}

def _client():
    load_dotenv()
    token = os.getenv("NOTION_TOKEN")
    db_id = os.getenv("NOTION_ALERT_DB_ID")
    if not token or not db_id:
        raise RuntimeError("NOTION_TOKEN 또는 NOTION_ALERT_DB_ID 누락")
    return Client(auth=token), db_id

def push(status:str, summary:str, started:datetime, ended:datetime=None, detail:str=""):
    notion, db_id = _client()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    host = socket.gethostname()
    props = {
        PROP["TITLE"]:   {"title":[{"text":{"content":f"[{status}] Notion Sync"}}]},
        PROP["SUMMARY"]: {"rich_text":[{"text":{"content":summary[:2000]}}]},
        PROP["STATUS"]:  {"select":{"name":status}},
        PROP["STARTED"]: {"date":{"start": started.isoformat()}},
        PROP["TIMESTAMP"]:{"date":{"start": now}},
        PROP["HOST"]:    {"rich_text":[{"text":{"content":host}}]},
    }
    if ended:
        props[PROP["ENDED"]] = {"date":{"start": ended.isoformat()}}

    notion.pages.create(parent={"database_id": db_id}, properties=props)