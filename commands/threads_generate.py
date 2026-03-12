"""원고 DB → Threads 게시글 자동 생성 → 노션 저장."""

import os
from lib import notion, ai


def run(keyword=None):
    """원고를 기반으로 숏폼 7개 + 롱폼 1개 + 체인 1세트 생성."""
    manuscript_db_id = os.getenv("NOTION_MANUSCRIPT_DB_ID", "")
    threads_db_id = os.getenv("NOTION_DATABASE_ID", "")

    if not manuscript_db_id:
        print("❌ NOTION_MANUSCRIPT_DB_ID 환경변수가 설정되지 않았습니다.")
        return

    # 1. 원고 선택
    page = _select_manuscript(manuscript_db_id, keyword)
    if not page:
        return

    page_id = page["id"]
    title = notion.get_prop_text(page, "제목") or notion.get_prop_text(page, "이름") or notion.get_prop_text(page, "Name")

    print(f"\n📄 선택된 원고: {title}")
    print("원고 본문 가져오는 중...")

    # 2. 원고 본문 가져오기
    manuscript_text = notion.get_page_content(page_id)
    if not manuscript_text.strip():
        print("❌ 원고 본문이 비어 있습니다.")
        return

    print(f"원고 길이: {len(manuscript_text)}자\n")

    # 3. 콘텐츠 생성
    print("🔄 숏폼 7개 생성 중...")
    shortforms = ai.generate_shortform(manuscript_text, title, count=7)
    print(f"  ✅ 숏폼 {len(shortforms)}개 생성 완료")

    print("🔄 롱폼 1개 생성 중...")
    longform = ai.generate_longform(manuscript_text, title)
    print("  ✅ 롱폼 생성 완료")

    print("🔄 체인 1세트 생성 중...")
    chain = ai.generate_chain(manuscript_text, title, parts=3)
    print(f"  ✅ 체인 {len(chain)}파트 생성 완료\n")

    # 4. 노션 저장
    saved = 0

    # 숏폼 저장
    print("💾 숏폼 노션 저장 중...")
    for i, sf in enumerate(shortforms, 1):
        hook = sf.get("hook", "")
        short_topic = hook[:20] if hook else f"#{i}"
        post_title = f"[{title}] #{i} - {short_topic}"
        props = {
            "제목": notion.set_title(post_title),
            "게시 타입": notion.set_select("숏폼"),
            "게시 상태": notion.set_status("대기"),
            "원본 원고": notion.set_relation([page_id]),
        }
        notion.create_page(threads_db_id, props, content_text=sf.get("text", ""))
        saved += 1
        print(f"  저장: {post_title}")

    # 롱폼 저장
    print("💾 롱폼 노션 저장 중...")
    longform_title = f"[{title}] - 롱폼"
    props = {
        "제목": notion.set_title(longform_title),
        "게시 타입": notion.set_select("롱폼"),
        "게시 상태": notion.set_status("대기"),
        "원본 원고": notion.set_relation([page_id]),
    }
    notion.create_page(threads_db_id, props, content_text=longform.get("text", ""))
    saved += 1
    print(f"  저장: {longform_title}")

    # 체인 저장
    print("💾 체인 노션 저장 중...")
    chain_title = f"[{title}] - 체인"
    chain_text = "\n\n---\n\n".join(c.get("text", "") for c in chain)
    props = {
        "제목": notion.set_title(chain_title),
        "게시 타입": notion.set_select("체인"),
        "게시 상태": notion.set_status("대기"),
        "원본 원고": notion.set_relation([page_id]),
    }
    notion.create_page(threads_db_id, props, content_text=chain_text)
    saved += 1
    print(f"  저장: {chain_title}")

    print(f"\n✅ 총 {saved}개 게시글이 노션에 저장되었습니다.")
    print("노션에서 마음에 드는 글의 '게시 승인' 버튼을 클릭해주세요.")


def _select_manuscript(manuscript_db_id, keyword=None):
    """원고 목록에서 선택 또는 키워드 검색."""
    if keyword:
        # 키워드로 검색
        filter_payload = {
            "property": "제목",
            "title": {"contains": keyword},
        }
        pages = notion.query_db(filter_payload, database_id=manuscript_db_id)
        if not pages:
            # "이름" 또는 "Name" 속성으로 재시도
            for prop_name in ["이름", "Name"]:
                filter_payload = {
                    "property": prop_name,
                    "title": {"contains": keyword},
                }
                try:
                    pages = notion.query_db(filter_payload, database_id=manuscript_db_id)
                    if pages:
                        break
                except Exception:
                    continue

        if not pages:
            print(f"❌ '{keyword}' 키워드로 원고를 찾을 수 없습니다.")
            return None

        if len(pages) == 1:
            return pages[0]

        return _show_list_and_select(pages)
    else:
        # 전체 목록
        pages = notion.query_db(database_id=manuscript_db_id)
        if not pages:
            print("❌ 원고 DB에 항목이 없습니다.")
            return None

        return _show_list_and_select(pages)


def _show_list_and_select(pages):
    """페이지 목록 출력 후 번호로 선택."""
    print(f"\n📋 원고 목록 ({len(pages)}건):")
    for i, page in enumerate(pages, 1):
        title = (
            notion.get_prop_text(page, "제목")
            or notion.get_prop_text(page, "이름")
            or notion.get_prop_text(page, "Name")
            or "(제목 없음)"
        )
        print(f"  {i}. {title}")

    while True:
        try:
            choice = input("\n번호를 입력하세요 (0=취소): ").strip()
            if choice == "0":
                print("취소되었습니다.")
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(pages):
                return pages[idx]
            print(f"1~{len(pages)} 사이 번호를 입력해주세요.")
        except (ValueError, EOFError):
            print("올바른 번호를 입력해주세요.")
            return None
