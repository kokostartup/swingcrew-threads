#!/usr/bin/env python3
"""스윙크루 Threads 자동 게시 CLI

사용법:
    python swingcrew.py status                      DB 현황 확인
    python swingcrew.py publish [all|제목] [--limit N]  승인된 글 Threads 게시
    python swingcrew.py report [YYYY-MM-DD]          성과 리포트 → Teams 전송 (기본: 전일)
"""

import sys
import os

from dotenv import load_dotenv
load_dotenv()

REQUIRED_ENV = {
    "status": ["NOTION_TOKEN", "NOTION_DATABASE_ID"],
    "publish": ["NOTION_TOKEN", "NOTION_DATABASE_ID", "THREADS_ACCESS_TOKEN", "THREADS_USER_ID", "THREADS_USERNAME"],
    "report": ["THREADS_ACCESS_TOKEN", "THREADS_USER_ID", "MS_TEAMS_WEBHOOK_URL"],
}


def check_env(command):
    """필수 환경변수 확인."""
    required = REQUIRED_ENV.get(command, [])
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        print(f"다음 환경변수가 설정되지 않았습니다:")
        for key in missing:
            print(f"  - {key}")
        print(f"\n.env 파일에 값을 입력해주세요.")
        return False
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()
    args = sys.argv[2:] if len(sys.argv) > 2 else []

    if not check_env(command):
        return

    if command == "status":
        from commands.threads_status import run
        run()

    elif command == "publish":
        from commands.threads_publish import run
        limit = 1
        filtered_args = []
        i = 0
        while i < len(args):
            if args[i] == "--limit" and i + 1 < len(args):
                limit = int(args[i + 1])
                i += 2
            else:
                filtered_args.append(args[i])
                i += 1
        target = " ".join(filtered_args) if filtered_args else "all"
        run(target=target, limit=limit)

    elif command == "report":
        from commands.threads_report import run
        report_date = args[0] if args else None
        run(report_date=report_date)

    else:
        print(f"알 수 없는 커맨드: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
