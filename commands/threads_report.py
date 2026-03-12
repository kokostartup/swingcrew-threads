"""전일 Threads 성과 리포트 + 트렌드 분석을 MS Teams로 발송."""

from datetime import date, timedelta
from lib import threads, teams, trends


def run():
    """전일 성과 + 트렌드 키워드 분석을 Teams로 전송."""
    yesterday = date.today() - timedelta(days=1)
    since = yesterday.isoformat()
    until = date.today().isoformat()

    print(f"📊 {since} 리포트 생성 중...")

    # ── 섹션 1: 내 게시물 성과 ──
    yesterday_posts = []
    try:
        yesterday_posts = threads.get_threads_with_insights(
            since=since, until=until, limit=100,
        )
        print(f"  내 게시물: {len(yesterday_posts)}건")
    except Exception as e:
        print(f"  ⚠️ 내 게시물 조회 실패: {e}")

    # ── 섹션 2: 실시간 인기 키워드 수집 (Google Trends) ──
    print("🔍 Google Trends 인기 키워드 수집 중...")
    trending_keywords = []
    try:
        trending_keywords = trends.get_trending_keywords(limit=10)
        print(f"  수집된 키워드: {trending_keywords}")
    except Exception as e:
        print(f"  ⚠️ 트렌드 키워드 수집 실패: {e}")

    # ── 섹션 3: 각 키워드를 Threads에서 검색 → 조회수 합산 → 순위 ──
    keyword_results = []
    if trending_keywords:
        print("🔍 Threads 키워드 검색 중...")
        keyword_results = _search_keywords_on_threads(trending_keywords)

    # Top 5 키워드 선정 (게시물이 실제로 있는 것만)
    top5_keywords = [k for k in keyword_results if k["post_count"] > 0][:5]

    # ── 섹션 4: Top 5 키워드 상세 분석 ──
    keyword_analysis = []
    if top5_keywords:
        print("📈 Top 5 키워드 상세 분석 중...")
        keyword_analysis = _analyze_top_keywords(top5_keywords)

    # ── 섹션 5: Top 3 인기 게시물 작성자 프로필 분석 ──
    author_analysis = []
    if top5_keywords:
        print("👤 인기 작성자 프로필 분석 중...")
        author_analysis = _analyze_top_authors(top5_keywords)

    # 리포트 본문 생성
    body = _build_report(since, yesterday_posts, trending_keywords,
                         keyword_results, keyword_analysis, author_analysis)

    print(body)
    print()

    # Teams 전송
    title = f"🏌️ 스윙크루 Threads 일일 리포트 ({since})"
    try:
        teams.send_message(title, body)
        print("✅ Teams 전송 완료")
    except Exception as e:
        print(f"❌ Teams 전송 실패: {e}")
        print("  리포트 데이터는 위 로그에서 확인 가능합니다.")


# ── 트렌드 분석 함수들 ──────────────────────────────────


def _search_keywords_on_threads(keywords):
    """각 키워드를 Threads에서 검색, Top 10 게시물 조회수 합산 후 순위 반환."""
    results = []
    for kw in keywords:
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
    """Top 5 키워드의 게시물 분석 요약."""
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
    """Top 5 키워드에서 조회수 Top 3 게시물 작성자의 게시물 분석.

    Note: Threads API 제한으로 다른 사용자의 프로필/게시물 직접 조회가 불가하므로,
          검색 결과 내에서 해당 작성자의 게시물을 모아서 분석합니다.
    """
    # 모든 게시물을 수집
    all_posts = []
    for kw_data in top5_keywords:
        all_posts.extend(kw_data.get("posts", []))

    # 작성자별 게시물 그룹핑
    author_posts = {}
    for post in all_posts:
        username = post.get("username", "")
        if not username:
            continue
        if username not in author_posts:
            author_posts[username] = []
        author_posts[username].append(post)

    # 작성자별 총 조회수 계산 → 상위 3명
    author_stats = []
    for username, posts in author_posts.items():
        total_views = sum(
            p.get("insights", {}).get("views", 0) for p in posts
        )
        total_likes = sum(
            p.get("insights", {}).get("likes", 0) for p in posts
        )
        total_replies = sum(
            p.get("insights", {}).get("replies", 0) for p in posts
        )
        # 조회수 최고 게시물
        best_post = max(
            posts, key=lambda p: p.get("insights", {}).get("views", 0)
        )
        author_stats.append({
            "username": username,
            "total_views": total_views,
            "total_likes": total_likes,
            "total_replies": total_replies,
            "post_count": len(posts),
            "best_post": best_post,
            "posts": sorted(
                posts,
                key=lambda p: p.get("insights", {}).get("views", 0),
                reverse=True,
            )[:5],
        })

    author_stats.sort(key=lambda x: x["total_views"], reverse=True)
    return author_stats[:3]


# ── 리포트 빌더 ─────────────────────────────────────────


def _build_report(report_date, yesterday_posts, trending_keywords,
                  keyword_results, keyword_analysis, author_analysis):
    """리포트 마크다운 생성."""
    lines = []

    # ── 섹션 1: 전일 내 게시물 성과 ──
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
            if not text_preview:
                text_preview = "(이미지 게시물)"
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

    # ── 섹션 2: 실시간 트렌드 키워드 (Google Trends → Threads 조회수) ──
    lines.append("## 🔥 실시간 트렌드 키워드 (Google Trends)")
    lines.append("")

    if not keyword_results:
        if trending_keywords:
            lines.append("키워드는 수집했으나 Threads 검색에 실패했습니다.")
            lines.append(f"수집 키워드: {', '.join(trending_keywords)}")
        else:
            lines.append("트렌드 키워드를 수집하지 못했습니다.")
    else:
        for i, kw in enumerate(keyword_results, 1):
            views_str = f"{kw['total_views']:,}" if kw["total_views"] > 0 else "데이터 없음"
            lines.append(
                f"**{i}.** {kw['keyword']} — "
                f"게시물 {kw['post_count']}건, 총 조회수 {views_str}"
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
            best_user = best.get("username", "")
            best_link = best.get("permalink", "")

            lines.append(f"**🏷 {ka['keyword']}** ({ka['post_count']}건)")
            lines.append(
                f"  평균 조회수: {ka['avg_views']:,} / "
                f"총 반응(좋아요+댓글): {ka['total_engagement']}"
            )
            if best_text:
                lines.append(
                    f"  🏆 베스트: @{best_user} — {best_text}... (👁 {best_views:,})"
                    + (f" [링크]({best_link})" if best_link else "")
                )
            lines.append("")

    lines.append("---")
    lines.append("")

    # ── 섹션 4: 인기 작성자 TOP 3 ──
    lines.append("## 👤 인기 작성자 TOP 3")
    lines.append("")

    if not author_analysis:
        lines.append("작성자 분석 데이터가 없습니다.")
    else:
        for i, author in enumerate(author_analysis, 1):
            username = author["username"]
            total_views = author.get("total_views", 0)
            total_likes = author.get("total_likes", 0)
            total_replies = author.get("total_replies", 0)
            post_count = author.get("post_count", 0)

            lines.append(f"**{i}. @{username}** (검색 내 게시물 {post_count}건)")
            lines.append(
                f"  총 조회수: 👁 {total_views:,} / "
                f"❤️ {total_likes} / 💬 {total_replies}"
            )

            # 해당 작성자의 인기 게시물
            posts = author.get("posts", [])
            if posts:
                lines.append("  인기 게시물:")
                for rp in posts[:3]:
                    rp_text = (rp.get("text") or "")[:40].replace("\n", " ")
                    if not rp_text:
                        rp_text = "(이미지)"
                    rp_views = rp.get("insights", {}).get("views", 0)
                    rp_link = rp.get("permalink", "")
                    lines.append(
                        f"    • {rp_text}... (👁 {rp_views:,})"
                        + (f" [링크]({rp_link})" if rp_link else "")
                    )
            lines.append("")

    return "\n".join(lines)
