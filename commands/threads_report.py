"""전일 Threads 성과 리포트 + 트렌드 분석을 MS Teams로 발송."""

from datetime import date, timedelta
from lib import threads, teams

# 골프 관련 트렌드 키워드 풀 (매일 전부 검색 → 조회수 상위 선정)
GOLF_KEYWORDS = [
    "골프 스윙", "드라이버 비거리", "골프 레슨", "골프 연습",
    "퍼팅", "아이언 샷", "골프 초보", "골프 루틴",
    "골프 피팅", "골프 클럽", "골프 라운드", "싱글 골퍼",
    "골프 그립", "체중이동", "백스윙", "다운스윙",
    "골프 유튜브", "골프 브이로그", "골프웨어", "골프장 추천",
]


def run():
    """전일 성과 + 트렌드 키워드 분석을 Teams로 전송."""
    yesterday = date.today() - timedelta(days=1)
    since = yesterday.isoformat()
    until = date.today().isoformat()

    print(f"📊 {since} 리포트 생성 중...")

    # ── 섹션 1: 내 게시물 성과 ──
    yesterday_posts = threads.get_threads_with_insights(
        since=since, until=until, limit=100,
    )

    # ── 섹션 2: 트렌드 키워드 분석 ──
    print("🔍 트렌드 키워드 검색 중...")
    keyword_results = _search_trending_keywords()

    # Top 5 키워드 선정
    top5_keywords = keyword_results[:5]

    # Top 5 키워드별 게시물 상세 분석
    print("📈 Top 5 키워드 게시물 분석 중...")
    keyword_analysis = _analyze_top_keywords(top5_keywords)

    # Top 3 게시물 작성자 프로필 분석
    print("👤 인기 게시물 작성자 프로필 분석 중...")
    author_analysis = _analyze_top_authors(top5_keywords)

    # 리포트 본문 생성
    body = _build_report(since, yesterday_posts, keyword_results,
                         keyword_analysis, author_analysis)

    print(body)
    print()

    # Teams 전송
    title = f"🏌️ 스윙크루 Threads 일일 리포트 ({since})"
    teams.send_message(title, body)
    print("✅ Teams 전송 완료")


def _search_trending_keywords():
    """모든 골프 키워드를 검색하고 조회수 합계로 정렬.

    Returns:
        list[dict]: [{keyword, total_views, post_count, posts}, ...]
                    조회수 내림차순 정렬.
    """
    results = []
    for kw in GOLF_KEYWORDS:
        try:
            posts, total_views = threads.search_keyword_with_views(kw, limit=10)
            results.append({
                "keyword": kw,
                "total_views": total_views,
                "post_count": len(posts),
                "posts": posts,
            })
            print(f"  '{kw}': {len(posts)}건, 조회수 합계 {total_views:,}")
        except Exception as e:
            print(f"  '{kw}': 검색 실패 - {e}")

    results.sort(key=lambda x: x["total_views"], reverse=True)
    return results


def _analyze_top_keywords(top5):
    """Top 5 키워드의 게시물 10개씩 분석 → 요약.

    Returns:
        list[dict]: [{keyword, avg_views, top_post_text, engagement_rate}, ...]
    """
    analysis = []
    for kw_data in top5:
        posts = kw_data["posts"]
        if not posts:
            continue

        views_list = [p.get("insights", {}).get("views", 0) for p in posts]
        likes_list = [p.get("insights", {}).get("likes", 0) for p in posts]
        replies_list = [p.get("insights", {}).get("replies", 0) for p in posts]

        total_views = sum(views_list)
        avg_views = total_views // len(posts) if posts else 0
        total_engagement = sum(likes_list) + sum(replies_list)

        # 조회수 1위 게시물
        best = max(posts, key=lambda p: p.get("insights", {}).get("views", 0))

        analysis.append({
            "keyword": kw_data["keyword"],
            "avg_views": avg_views,
            "total_engagement": total_engagement,
            "best_post": best,
            "post_count": len(posts),
        })
    return analysis


def _analyze_top_authors(top5_keywords):
    """Top 5 키워드에서 조회수 Top 3 게시물의 작성자 프로필 + 전일 게시글 분석.

    Returns:
        list[dict]: [{username, profile, recent_posts}, ...]
    """
    # 모든 Top 5 키워드의 게시물을 조회수순으로 모으기
    all_posts = []
    for kw_data in top5_keywords:
        all_posts.extend(kw_data.get("posts", []))

    # 조회수 Top 3 게시물 (중복 작성자 제거)
    all_posts.sort(
        key=lambda p: p.get("insights", {}).get("views", 0), reverse=True
    )
    seen_users = set()
    top_authors = []
    for post in all_posts:
        username = post.get("username", "")
        user_id = post.get("id", "").split("_")[0] if "_" in post.get("id", "") else ""
        if not username or username in seen_users:
            continue
        seen_users.add(username)
        top_authors.append(post)
        if len(top_authors) >= 3:
            break

    # 각 작성자 프로필 + 최근 게시물 조회
    results = []
    for post in top_authors:
        username = post.get("username", "unknown")
        author_id = post.get("id", "")

        profile = {"username": username}
        recent_posts = []

        # 프로필 조회 시도 (실패해도 계속)
        try:
            profile = threads.get_user_profile(author_id)
        except Exception:
            pass

        # 최근 게시물 조회 시도
        try:
            recent_posts = threads.get_user_recent_threads(author_id, limit=5)
        except Exception:
            pass

        results.append({
            "username": username,
            "profile": profile,
            "recent_posts": recent_posts,
            "top_post": post,
        })

    return results


def _build_report(report_date, yesterday_posts, keyword_results,
                  keyword_analysis, author_analysis):
    """리포트 마크다운 생성."""
    lines = []

    # ── 섹션 1: 전일 게시물 성과 ──
    lines.append(f"## 📅 {report_date} 내 게시물 성과")
    lines.append("")

    if not yesterday_posts:
        lines.append("전일 게시된 글이 없습니다.")
    else:
        total_views = 0
        total_likes = 0
        total_replies = 0

        for p in yesterday_posts:
            ins = p.get("insights", {})
            views = ins.get("views", 0)
            likes = ins.get("likes", 0)
            replies = ins.get("replies", 0)
            reposts = ins.get("reposts", 0)
            quotes = ins.get("quotes", 0)
            total_views += views
            total_likes += likes
            total_replies += replies

            text_preview = (p.get("text") or "")[:60].replace("\n", " ")
            lines.append(f"- **{text_preview}...**")
            lines.append(
                f"  👁 {views:,}  ❤️ {likes}  💬 {replies}  🔄 {reposts}  📝 {quotes}"
            )

        lines.append("")
        lines.append(
            f"**합계**: 👁 {total_views:,} 조회 / "
            f"❤️ {total_likes} 좋아요 / 💬 {total_replies} 댓글"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # ── 섹션 2: 트렌드 키워드 TOP 10 ──
    lines.append("## 🔥 트렌드 키워드 TOP 10")
    lines.append("")

    top10 = keyword_results[:10]
    if not top10:
        lines.append("키워드 검색 결과가 없습니다.")
    else:
        for i, kw in enumerate(top10, 1):
            lines.append(
                f"**{i}.** {kw['keyword']} — "
                f"게시물 {kw['post_count']}건, 총 조회수 {kw['total_views']:,}"
            )

    lines.append("")
    lines.append("---")
    lines.append("")

    # ── 섹션 3: Top 5 키워드 상세 분석 ──
    lines.append("## 📈 Top 5 키워드 상세 분석")
    lines.append("")

    if not keyword_analysis:
        lines.append("분석 데이터가 없습니다.")
    else:
        for ka in keyword_analysis:
            best = ka.get("best_post", {})
            best_text = (best.get("text") or "")[:50].replace("\n", " ")
            best_views = best.get("insights", {}).get("views", 0)
            best_link = best.get("permalink", "")

            lines.append(f"**🏷 {ka['keyword']}**")
            lines.append(
                f"  평균 조회수: {ka['avg_views']:,} / "
                f"총 반응(좋아요+댓글): {ka['total_engagement']}"
            )
            lines.append(
                f"  🏆 베스트: {best_text}... (👁 {best_views:,})"
                + (f" [링크]({best_link})" if best_link else "")
            )
            lines.append("")

    lines.append("---")
    lines.append("")

    # ── 섹션 4: 인기 게시물 작성자 TOP 3 프로필 분석 ──
    lines.append("## 👤 인기 작성자 TOP 3 프로필")
    lines.append("")

    if not author_analysis:
        lines.append("작성자 프로필 데이터가 없습니다.")
    else:
        for i, author in enumerate(author_analysis, 1):
            username = author["username"]
            profile = author.get("profile", {})
            bio = profile.get("threads_biography", "")
            name = profile.get("name", username)
            top_post = author.get("top_post", {})
            top_views = top_post.get("insights", {}).get("views", 0)

            lines.append(f"**{i}. @{username}** ({name})")
            if bio:
                lines.append(f"  소개: {bio[:80]}")
            lines.append(f"  인기 게시물 조회수: 👁 {top_views:,}")

            # 최근 게시물
            recent = author.get("recent_posts", [])
            if recent:
                lines.append(f"  최근 게시물 {len(recent)}건:")
                for rp in recent[:3]:
                    rp_text = (rp.get("text") or "")[:40].replace("\n", " ")
                    rp_link = rp.get("permalink", "")
                    lines.append(
                        f"    • {rp_text}..."
                        + (f" [링크]({rp_link})" if rp_link else "")
                    )
            lines.append("")

    return "\n".join(lines)
