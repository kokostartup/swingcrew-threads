"""웹에서 골프 뉴스 검색 → 게시글 생성 → 노션 저장."""

import os
from lib import notion, ai


def run(keyword=None):
    """골프 뉴스 게시글 생성 → 노션 저장."""
    threads_db_id = os.getenv("NOTION_DATABASE_ID", "")

    print("🏌️ 골프 소식 게시글 생성 중...\n")

    # Claude로 뉴스 게시글 생성
    posts = ai.generate_news_posts(topic=keyword, count=4)
    print(f"✅ {len(posts)}개 게시글 생성 완료\n")

    # 노션 저장
    print("💾 노션 저장 중...")
    saved = 0
    for i, post in enumerate(posts, 1):
        hook = post.get("hook", "")
        topic_label = keyword or hook[:15] or f"소식{i}"
        post_title = f"[{topic_label}] - 골프소식"

        props = {
            "제목": notion.set_title(post_title),
            "게시 타입": notion.set_select("골프소식"),
            "게시 상태": notion.set_status("대기"),
        }
        notion.create_page(threads_db_id, props, content_text=post.get("text", ""))
        saved += 1
        print(f"  저장: {post_title}")

    print(f"\n✅ {saved}개 골프 소식 게시글이 노션에 저장되었습니다.")
    print("노션에서 확인 후 '게시 승인' 버튼을 클릭해주세요.")
