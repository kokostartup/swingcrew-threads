#!/usr/bin/env python3
"""스윙크루 Threads 자동화 CLI

사용법:
    python swingcrew.py status                  DB 현황 확인
    python swingcrew.py generate [키워드]       원고 → 게시글 생성
    python swingcrew.py publish [all|제목]      승인된 글 Threads 게시
    python swingcrew.py news [키워드]           골프 뉴스 게시글 생성
    python swingcrew.py video <URL|제목>        영상 코멘트 생성
"""

import sys
import os

# .env 로드
from dotenv import load_dotenv
load_dotenv()

# 환경변수 검증
REQUIRED_ENV = {
    "status": ["NOTION_TOKEN", "NOTION_DATABASE_ID"],
    "generate": ["NOTION_TOKEN", "NOTION_DATABASE_ID", "NOTION_MANUSCRIPT_DB_ID", "ANTHROPIC_API_KEY"],
    "publish": ["NOTION_TOKEN", "NOTION_DATABASE_ID", "THREADS_ACCESS_TOKEN", "THREADS_USER_ID", "THREADS_USERNAME"],
    "news": ["NOTION_TOKEN", "NOTION_DATABASE_ID", "ANTHROPIC_API_KEY"],
    "video": ["NOTION_TOKEN", "NOTION_DATABASE_ID", "ANTHROPIC_API_KEY"],
}


def check_env(command):
    """필수 환경변수 확인."""
    required = REQUIRED_ENV.get(command, [])
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        print(f"❌ 다음 환경변수가 설정되지 않았습니다:")
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

    elif command == "generate":
        from commands.threads_generate import run
        keyword = " ".join(args) if args else None
        run(keyword=keyword)

    elif command == "publish":
        from commands.threads_publish import run
        target = " ".join(args) if args else "all"
        run(target=target)

    elif command == "news":
        from commands.threads_news import run
        keyword = " ".join(args) if args else None
        run(keyword=keyword)

    elif command == "video":
        from commands.threads_video import run
        url_or_title = " ".join(args) if args else None
        run(url_or_title=url_or_title)

    else:
        print(f"❌ 알 수 없는 커맨드: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
