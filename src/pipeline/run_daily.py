# src/pipeline/run_daily.py  (운영형: Alerts DB에 RUNNING/SUCCESS/FAILED 기록)
import sys, traceback
from datetime import datetime
from dotenv import load_dotenv

from src.utils.report_merge import main as merge_reports
from src.utils.notion_report_sync import main as sync_notion
from src.utils.notion_alert import push  # ← Alerts DB 모듈

def main():
    load_dotenv()
    started = datetime.now()

    # RUNNING 로그
    try:
        push("RUNNING", "Pipeline started", started)
    except Exception:
        pass  # 알림 실패해도 파이프라인은 진행

    try:
        print(f"[START] {started.isoformat()}")

        print("[STEP] Merging reports...")
        merge_reports()

        print("[STEP] Syncing to Notion...")
        sync_notion()

        ended = datetime.now()
        try:
            push("SUCCESS", "Pipeline finished OK", started, ended)
        finally:
            print("[DONE] All daily tasks completed!")

    except Exception as e:
        ended = datetime.now()
        detail = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        try:
            push("FAILED", detail[:1900], started, ended)
        finally:
            print(detail, file=sys.stderr)
        raise

if __name__ == "__main__":
    main()