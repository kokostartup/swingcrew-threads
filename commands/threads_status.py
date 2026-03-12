"""노션 Threads 게시글 DB 현황 출력."""

from lib import notion


def run():
    """DB 현황을 상태별로 요약 출력."""
    print("📊 Threads 게시글 DB 현황 조회 중...\n")

    pages = notion.query_db()

    # 상태별 분류
    status_map = {"대기": [], "승인": [], "게시완료": [], "실패": []}
    for page in pages:
        status = notion.get_prop_select(page, "게시 상태")
        title = notion.get_prop_text(page, "제목")
        post_type = notion.get_prop_select(page, "게시 타입")
        if status in status_map:
            status_map[status].append({"title": title, "type": post_type, "page": page})
        else:
            status_map.setdefault("기타", []).append({"title": title, "type": post_type, "page": page})

    # 요약 출력
    print("=" * 50)
    print(f"  대기:     {len(status_map['대기'])}건")
    print(f"  승인:     {len(status_map['승인'])}건 (게시 예정)")
    print(f"  게시완료: {len(status_map['게시완료'])}건")
    print(f"  실패:     {len(status_map['실패'])}건")
    print(f"  전체:     {len(pages)}건")
    print("=" * 50)

    # 승인 대기 목록
    if status_map["대기"]:
        print(f"\n⏳ 승인 대기 ({len(status_map['대기'])}건):")
        for item in status_map["대기"]:
            print(f"  - [{item['type']}] {item['title']}")

    # 승인됨 (게시 예정)
    if status_map["승인"]:
        print(f"\n✅ 게시 예정 ({len(status_map['승인'])}건):")
        for item in status_map["승인"]:
            print(f"  - [{item['type']}] {item['title']}")

    # 실패 항목
    if status_map["실패"]:
        print(f"\n❌ 실패 ({len(status_map['실패'])}건):")
        for item in status_map["실패"]:
            memo = notion.get_prop_text(item["page"], "메모")
            print(f"  - [{item['type']}] {item['title']}")
            if memo:
                print(f"    사유: {memo}")

    if not pages:
        print("\n(DB에 게시글이 없습니다)")

    print()
