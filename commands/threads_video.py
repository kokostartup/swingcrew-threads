"""유튜브 영상 코멘트 게시글 생성 → 노션 저장 (상태: 승인)."""

import os
from lib import notion, ai


def run(url_or_title=None):
    """영상 코멘트 생성 → 노션 저장 (즉시 게시 예정)."""
    threads_db_id = os.getenv("NOTION_DATABASE_ID", "")
    manuscript_db_id = os.getenv("NOTION_MANUSCRIPT_DB_ID", "")

    if not url_or_title:
        print("❌ 유튜브 영상 URL 또는 제목을 인자로 입력해주세요.")
        print("사용법: python swingcrew.py video <URL 또는 영상제목>")
        return

    # URL인지 제목인지 판별
    is_url = url_or_title.startswith("http")
    video_url = url_or_title if is_url else ""
    video_title = url_or_title if not is_url else ""

    if is_url:
        # URL에서 제목 추출은 어려우므로 사용자 입력 그대로 사용
        video_title = url_or_title

    print(f"🎬 영상 코멘트 생성 중...")
    print(f"  영상: {url_or_title}\n")

    # 원고 DB에서 관련 원고 검색 (선택적)
    manuscript_text = ""
    if manuscript_db_id and not is_url:
        manuscript_text = _find_related_manuscript(manuscript_db_id, video_title)

    # 코멘트 생성
    result = ai.generate_video_comment(video_title, video_url, manuscript_text)
    comment_text = result.get("text", "")

    if not comment_text:
        print("❌ 코멘트 생성에 실패했습니다.")
        return

    print("생성된 코멘트:")
    print(f"{'─' * 40}")
    print(comment_text)
    print(f"{'─' * 40}\n")

    # 노션 저장 (상태: 승인 — 즉시 게시용)
    post_title = f"[{video_title[:30]}] - 영상코멘트"
    props = {
        "제목": notion.set_title(post_title),
        "게시 타입": notion.set_select("영상코멘트"),
        "게시 상태": notion.set_status("승인"),
    }

    # 관련 원고가 있으면 relation 추가
    notion.create_page(threads_db_id, props, content_text=comment_text)

    print(f"✅ '{post_title}'이 '승인' 상태로 노션에 저장되었습니다.")
    print("다음 자동 게시 시간에 Threads에 올라갑니다.")
    print("바로 게시하려면: python swingcrew.py publish all")


def _find_related_manuscript(manuscript_db_id, search_term):
    """원고 DB에서 관련 원고 검색."""
    try:
        for prop_name in ["제목", "이름", "Name"]:
            filter_payload = {
                "property": prop_name,
                "title": {"contains": search_term[:20]},
            }
            try:
                pages = notion.query_db(filter_payload, database_id=manuscript_db_id)
                if pages:
                    content = notion.get_page_content(pages[0]["id"])
                    if content:
                        print(f"  📄 관련 원고 발견: {notion.get_prop_text(pages[0], prop_name)}")
                        return content
            except Exception:
                continue
    except Exception:
        pass
    return ""
