# src/utils/report_merge.py
from pathlib import Path
from datetime import datetime
import re

ROOT = Path(__file__).resolve().parents[2]  # repo 루트
REPORTS = ROOT / "reports"
OUT = REPORTS / "AutoTraderAgent_Report_ALL.md"

DAY_PATTERN = re.compile(r"AutoTraderAgent_Day(\d+)_Report\.md", re.I)

def collect_day_reports():
    files = []
    for p in REPORTS.glob("AutoTraderAgent_Day*_Report.md"):
        m = DAY_PATTERN.match(p.name)
        if m:
            files.append((int(m.group(1)), p))
    return [p for _, p in sorted(files, key=lambda x: x[0])]

def build_toc(entries):
    lines = ["# AutoTraderAgent 종합 리포트 (ALL)",
             f"> 생성시각: {datetime.now():%Y-%m-%d %H:%M}\n",
             "## 목차"]
    for i, p in enumerate(entries, 1):
        day = DAY_PATTERN.match(p.name).group(1)
        lines.append(f"{i}. [Day{day} 리포트](#day{day}-리포트)")
    lines.append("\n---\n")
    return "\n".join(lines)

def normalize_heading(md_text, day):
    # 최상단에 앵커용 헤딩 삽입
    header = f"\n\n## Day{day} 리포트\n\n"
    return header + md_text.strip() + "\n"

def main():
    entries = collect_day_reports()
    if not entries:
        print("리포트 파일을 찾지 못했습니다.")
        return

    toc = build_toc(entries)
    body_parts = []
    for p in entries:
        day = DAY_PATTERN.match(p.name).group(1)
        text = p.read_text(encoding="utf-8", errors="ignore")
        body_parts.append(normalize_heading(text, day))

    OUT.write_text(toc + "\n".join(body_parts), encoding="utf-8")
    print(f"[OK] 통합 리포트 생성: {OUT}")

if __name__ == "__main__":
    main()