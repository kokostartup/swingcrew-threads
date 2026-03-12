"""전일 Threads 성과 리포트를 MS Teams로 발송."""

from datetime import date, timedelta
from lib import threads, teams


def run():
    """전일 게시물 인사이트 + 인기 게시물 TOP 10을 Teams로 전송."""
    yesterday = date.today() - timedelta(days=1)
    since = yesterday.isoformat()
    until = date.today().isoformat()

    print(f"📊 {since} 리포트 생성 중...")

    # 전일 게시물 인사이트
    yesterday_posts = threads.get_threads_with_insights(
        since=since, until=until, limit=100,
    )

    # 최근 전체 게시물 중 조회수 TOP 10 (인기/트렌드)
    all_recent = threads.get_threads_with_insights(limit=50)
    top_posts = sorted(
        [p for p in all_recent if p.get("insights")],
        key=lambda p: p["insights"].get("views", 0),
        reverse=True,
    )[:10]

    # 리포트 본문 생성
    body = _build_report(since, yesterday_posts, top_posts)

    print(body)
    print()

    # Teams 전송
    title = f"🏌️ 스윙크루 Threads 일일 리포트 ({since})"
    teams.send_message(title, body)
    print(f"✅ Teams 전송 완료")


def _build_report(report_date, yesterday_posts, top_posts):
    """리포트 마크다운 생성."""
    lines = []

    # ── 섹션 1: 전일 게시물 성과 ──
    lines.append(f"## 📅 {report_date} 게시물 성과")
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
            lines.append(
                f"- **{text_preview}...**"
            )
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

    # ── 섹션 2: 인기 게시물 TOP 10 ──
    lines.append("## 🔥 인기 게시물 TOP 10 (조회수 기준)")
    lines.append("")

    if not top_posts:
        lines.append("인사이트 데이터가 없습니다.")
    else:
        for i, p in enumerate(top_posts, 1):
            ins = p.get("insights", {})
            views = ins.get("views", 0)
            likes = ins.get("likes", 0)
            replies = ins.get("replies", 0)
            text_preview = (p.get("text") or "")[:50].replace("\n", " ")
            permalink = p.get("permalink", "")

            lines.append(f"**{i}.** {text_preview}...")
            lines.append(
                f"   👁 {views:,}  ❤️ {likes}  💬 {replies}"
                + (f"  [링크]({permalink})" if permalink else "")
            )

    return "\n".join(lines)
