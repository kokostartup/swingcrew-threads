"""유튜브 영상 코멘트 Threads 게시글 생성."""

import os
from lib import notion, ai


THREADS_DB_ID = os.getenv("NOTION_DATABASE_ID", "")
MANUSCRIPT_DB_ID = os.getenv("NOTION_MANUSCRIPT_DB_ID", "")


def run(url_or_title=None):
    """영상 코멘트 게시글 생성 → 노션 저장 (승인 상태)."""
    if not url_or_title:
        print("사용법: python swingcrew.py video <유튜브URL 또는 영상제목>")
        return

    # URL인지 제목인지 구분
    if "youtube.com" in url_or_title or "youtu.be" in url_or_title:
        video_url = url_or_title
        video_title = input("영상 제목을 입력해주세요: ").strip()
        if not video_title:
            print("영상 제목이 필요합니다.")
            return
    else:
        video_title = url_or_title
        video_url = input("영상 URL을 입력해주세요 (없으면 Enter): ").strip()

    # 관련 원고 검색
    manuscript_text = ""
    if MANUSCRIPT_DB_ID:
        print("관련 원고 검색 중...")
        try:
            filter_payload = {
                "property": "제목",
                "title": {"contains": video_title[:20]},
            }
            pages = notion.query_db(filter_payload, database_id=MANUSCRIPT_DB_ID)
            if not pages:
                filter_payload = {
                    "property": "이름",
                    "title": {"contains": video_title[:20]},
                }
                pages = notion.query_db(filter_payload, database_id=MANUSCRIPT_DB_ID)
            if pages:
                manuscript_text = notion.get_page_content(pages[0]["id"])
                title = notion.get_prop_text(pages[0], "제목") or notion.get_prop_text(pages[0], "이름")
                print(f"  관련 원고 발견: {title}")
        except Exception as e:
            print(f"  원고 검색 실패: {e}")

    # 코멘트 생성
    print("\n영상 코멘트 생성 중...")
    try:
        comment = ai.generate_video_comment(video_title, video_url, manuscript_text)
        print(f"\n{'─' * 40}")
        print(comment)
        print(f"{'─' * 40}\n")
    except Exception as e:
        print(f"생성 실패: {e}")
        return

    # 노션 저장 (승인 상태 — 즉시 게시용)
    post_title = f"[{video_title}] - 영상코멘트"
    try:
        properties = {
            "제목": notion.set_title(post_title),
            "게시 타입": notion.set_select("영상코멘트"),
            "게시 상태": notion.set_select("승인"),
        }
        notion.create_page(THREADS_DB_ID, properties, comment)
        print(f"노션 저장 완료: {post_title}")
        print("'승인' 상태로 저장되었습니다. 다음 자동 게시 시간에 Threads에 올라갑니다.")
        print("바로 게시하려면: python swingcrew.py publish")
    except Exception as e:
        print(f"노션 저장 실패: {e}")
