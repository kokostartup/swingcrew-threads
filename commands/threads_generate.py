"""원고 기반 Threads 게시글 생성 (숏폼/롱폼/체인)."""

import os
from lib import notion, ai


THREADS_DB_ID = os.getenv("NOTION_DATABASE_ID", "")
MANUSCRIPT_DB_ID = os.getenv("NOTION_MANUSCRIPT_DB_ID", "")


def run(keyword=None):
    """원고를 선택하고, 숏폼/롱폼/체인 게시글을 생성하여 노션에 저장."""
    if not MANUSCRIPT_DB_ID:
        print("NOTION_MANUSCRIPT_DB_ID 환경변수가 설정되지 않았습니다.")
        return

    # 1. 원고 선택
    manuscript = _select_manuscript(keyword)
    if not manuscript:
        return

    page_id = manuscript["id"]
    title = notion.get_prop_text(manuscript, "제목") or notion.get_prop_text(manuscript, "이름")
    print(f"\n선택된 원고: {title}")

    # 2. 원고 본문 가져오기
    print("원고 본문 가져오는 중...")
    content = notion.get_page_content(page_id)
    if not content.strip():
        print("원고 본문이 비어 있습니다.")
        return
    print(f"  본문 길이: {len(content)}자\n")

    # 3. 숏폼 생성
    print("=" * 50)
    print("[1/3] 숏폼 생성 중 (7개)...")
    try:
        shortforms = ai.generate_shortform(content, title, count=7)
        print(f"  {len(shortforms)}개 생성 완료")
        for i, sf in enumerate(shortforms, 1):
            _save_to_notion(
                title=f"[{title}] #{i} - {sf['title']}",
                content_text=sf["text"],
                post_type="숏폼",
                manuscript_id=page_id,
            )
            print(f"  #{i} 저장: {sf['title']}")
    except Exception as e:
        print(f"  숏폼 생성 실패: {e}")

    # 4. 롱폼 생성
    print(f"\n{'=' * 50}")
    print("[2/3] 롱폼 생성 중 (1개)...")
    try:
        longform = ai.generate_longform(content, title)
        _save_to_notion(
            title=f"[{title}] - 롱폼",
            content_text=longform["text"],
            post_type="롱폼",
            manuscript_id=page_id,
        )
        print(f"  저장 완료 (훅: {longform['hook'][:50]}...)")
    except Exception as e:
        print(f"  롱폼 생성 실패: {e}")

    # 5. 체인 생성
    print(f"\n{'=' * 50}")
    print("[3/3] 체인 생성 중 (3파트)...")
    try:
        chain_parts = ai.generate_chain(content, title, parts=3)
        chain_text = "\n\n---\n\n".join(chain_parts)
        _save_to_notion(
            title=f"[{title}] - 체인",
            content_text=chain_text,
            post_type="체인",
            manuscript_id=page_id,
        )
        print(f"  {len(chain_parts)}파트 저장 완료")
    except Exception as e:
        print(f"  체인 생성 실패: {e}")

    # 6. 완료 안내
    print(f"\n{'=' * 50}")
    print("생성 완료!")
    print("노션에서 마음에 드는 글의 게시 상태를 '승인'으로 변경해주세요.")
    print("하루 5번 자동으로 Threads에 게시됩니다.")


def _select_manuscript(keyword=None):
    """원고 DB에서 원고를 선택."""
    if keyword:
        # 키워드로 원고 검색
        filter_payload = {
            "property": "제목",
            "title": {"contains": keyword},
        }
        pages = notion.query_db(filter_payload, database_id=MANUSCRIPT_DB_ID)
        if not pages:
            # 이름 속성으로도 시도
            filter_payload = {
                "property": "이름",
                "title": {"contains": keyword},
            }
            pages = notion.query_db(filter_payload, database_id=MANUSCRIPT_DB_ID)

        if not pages:
            print(f"'{keyword}' 키워드의 원고를 찾을 수 없습니다.")
            return None
        if len(pages) == 1:
            return pages[0]
        # 여러 개면 목록 표시
        return _show_and_select(pages)
    else:
        # 최근 원고 목록 표시
        sorts = [{"timestamp": "last_edited_time", "direction": "descending"}]
        pages = notion.query_db(database_id=MANUSCRIPT_DB_ID, sorts=sorts)
        if not pages:
            print("원고 DB에 항목이 없습니다.")
            return None
        return _show_and_select(pages)


def _show_and_select(pages):
    """원고 목록을 보여주고 번호로 선택."""
    print("\n원고 목록:")
    display = pages[:20]  # 최대 20개
    for i, page in enumerate(display, 1):
        title = notion.get_prop_text(page, "제목") or notion.get_prop_text(page, "이름")
        print(f"  {i:2d}. {title}")

    try:
        choice = input(f"\n번호를 입력하세요 (1~{len(display)}): ").strip()
        idx = int(choice) - 1
        if 0 <= idx < len(display):
            return display[idx]
        print("잘못된 번호입니다.")
    except (ValueError, EOFError):
        print("입력이 취소되었습니다.")
    return None


def _save_to_notion(title, content_text, post_type, manuscript_id=None):
    """게시글을 노션 Threads DB에 저장."""
    properties = {
        "제목": notion.set_title(title),
        "게시 타입": notion.set_select(post_type),
        "게시 상태": notion.set_select("대기"),
    }
    if manuscript_id:
        properties["원본 원고"] = notion.set_relation(manuscript_id)

    notion.create_page(THREADS_DB_ID, properties, content_text)
