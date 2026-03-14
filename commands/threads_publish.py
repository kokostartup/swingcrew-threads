"""노션에서 '승인' 상태 게시글을 Threads에 게시."""

import os
from datetime import date
from lib import notion, threads


def run(target="all", limit=0):
    """승인된 게시글을 Threads에 게시.

    Args:
        target: "all" 또는 특정 제목 키워드.
        limit: 게시할 최대 건수 (0이면 전체).
    """
    username = os.getenv("THREADS_USERNAME", "")

    # 승인 상태 항목 조회 (생성일 오름차순 — 오래된 것부터)
    filter_payload = {
        "property": "게시 상태",
        "select": {"equals": "승인"},
    }
    sorts = [{"timestamp": "created_time", "direction": "ascending"}]
    pages = notion.query_db(filter_payload, sorts=sorts)

    if not pages:
        print("현재 승인 대기 중인 게시글이 없습니다.")
        return

    # target이 특정 제목이면 필터링
    if target != "all":
        pages = [p for p in pages if target in notion.get_prop_text(p, "제목")]
        if not pages:
            print(f"'{target}' 제목의 승인된 게시글을 찾을 수 없습니다.")
            return

    print(f"📤 승인된 항목: {len(pages)}건\n")

    success_count = 0
    fail_count = 0
    skip_count = 0

    for page in pages:
        # limit 도달 시 종료 (성공 건수 기준)
        if limit > 0 and success_count >= limit:
            break

        page_id = page["id"]
        title = notion.get_prop_text(page, "제목")
        post_type = notion.get_prop_select(page, "게시 타입")
        image_status = notion.get_prop_select(page, "이미지 상태")
        image_url = notion.get_prop_files(page, "이미지") if image_status == "완료" else ""

        print(f"{'─' * 40}")
        print(f"📝 [{post_type}] {title}")

        try:
            content = notion.get_page_content(page_id)
            if not content.strip():
                print("  ⚠️ 본문이 비어 있습니다. 건너뜁니다.")
                skip_count += 1
                continue

            if post_type == "체인":
                _publish_chain(page_id, title, content, username)
            elif post_type == "롱폼" and len(content) > 500:
                _handle_longform(content, title)
                skip_count += 1
                continue
            else:
                _publish_single(page_id, title, content, image_url, username)

            success_count += 1

        except Exception as e:
            print(f"  ❌ 게시 실패: {e}")
            _mark_failed(page_id, str(e))
            fail_count += 1

    print(f"\n{'=' * 40}")
    print(f"📊 결과: 성공 {success_count} / 실패 {fail_count} / 건너뜀 {skip_count}")


def _publish_single(page_id, title, content, image_url, username):
    """단일 게시글 (숏폼/골프소식/영상코멘트) 게시."""
    print("  게시 중...")

    if image_url:
        post_id = threads.post_image(content, image_url)
    else:
        post_id = threads.post_text(content)

    url = threads.get_thread_url(post_id, username)
    print(f"  ✅ 게시 완료: {url}")

    # 노션 업데이트
    notion.update_page(page_id, {
        "게시 상태": notion.set_status("게시완료"),
        "게시일": notion.set_date(date.today().isoformat()),
        "Threads URL": notion.set_url(url),
    })


def _publish_chain(page_id, title, content, username):
    """체인(글타래) 게시 — 답글 연결 방식."""
    parts = [p.strip() for p in content.split("---") if p.strip()]
    if not parts:
        raise ValueError("체인 파트를 분리할 수 없습니다.")

    print(f"  체인 {len(parts)}파트 게시 중...")
    post_ids = threads.post_chain(parts)

    first_url = threads.get_thread_url(post_ids[0], username)
    print(f"  ✅ 체인 게시 완료: {first_url}")

    # 노션 업데이트
    notion.update_page(page_id, {
        "게시 상태": notion.set_status("게시완료"),
        "게시일": notion.set_date(date.today().isoformat()),
        "Threads URL": notion.set_url(first_url),
    })


def _handle_longform(content, title):
    """롱폼 게시글 — 500자 초과로 수동 게시 안내."""
    print(f"  ⚠️ 롱폼 ({len(content)}자) — Threads API 500자 제한으로 수동 게시 필요")
    print()
    print("  ┌─ 게시글 내용 ─────────────────────────")
    for line in content.split("\n"):
        print(f"  │ {line}")
    print("  └────────────────────────────────────────")
    print()
    print("  👉 위 내용을 Threads 앱에서 직접 붙여넣기 해주세요.")


def _mark_failed(page_id, error_msg):
    """실패 상태로 노션 업데이트."""
    try:
        notion.update_page(page_id, {
            "게시 상태": notion.set_status("실패"),
            "메모": notion.set_text(error_msg[:200]),
        })
    except Exception:
        pass
