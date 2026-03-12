"""최신 골프 소식 기반 Threads 게시글 생성."""

import os
from lib import notion, ai


THREADS_DB_ID = os.getenv("NOTION_DATABASE_ID", "")

# 기본 골프 뉴스 주제
DEFAULT_TOPICS = [
    "PGA Tour LPGA KPGA 최신 소식 2026",
    "골프 장비 신제품 규제 2026",
    "아마추어 골퍼 트렌드 골프 룰 변경",
]


def run(keyword=None):
    """골프 소식을 기반으로 Threads 게시글 생성 → 노션 저장."""
    # 1. 뉴스 주제 결정
    if keyword:
        topics_text = f"골프 관련 주제: {keyword}"
        print(f"주제: {keyword}")
    else:
        topics_text = "다음 주제들에 대한 최신 골프 소식을 작성해줘:\n"
        topics_text += "\n".join(f"- {t}" for t in DEFAULT_TOPICS)
        print("기본 골프 뉴스 주제로 생성합니다.")

    # 2. 게시글 생성
    print("\n골프소식 게시글 생성 중...")
    try:
        posts = ai.generate_news_posts(topics_text, count=4)
        print(f"  {len(posts)}개 생성 완료\n")
    except Exception as e:
        print(f"생성 실패: {e}")
        return

    # 3. 노션 저장
    saved = 0
    for post in posts:
        try:
            post_title = f"[{post['title']}] - 골프소식"
            properties = {
                "제목": notion.set_title(post_title),
                "게시 타입": notion.set_select("골프소식"),
                "게시 상태": notion.set_select("대기"),
            }
            notion.create_page(THREADS_DB_ID, properties, post["text"])
            print(f"  저장: {post_title}")
            saved += 1
        except Exception as e:
            print(f"  저장 실패 ({post.get('title', '?')}): {e}")

    print(f"\n{saved}개 골프소식이 노션에 저장되었습니다.")
    print("노션에서 확인 후 게시 상태를 '승인'으로 변경해주세요.")
