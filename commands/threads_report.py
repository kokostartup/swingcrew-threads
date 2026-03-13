"""전일 Threads 성과 리포트를 MS Teams로 발송."""

import sys
from datetime import date, datetime, timedelta
from lib import threads, teams


def run(report_date=None):
    """전일 게시물 인사이트 + 인기 게시물 TOP 10을 Teams로 전송.

    Args:
        report_date: 리포트 날짜 문자열 (YYYY-MM-DD). None이면 전일.
    """
    try:
        _run_report(report_date)
    except Exception as e:
        print(f"❌ 리포트 생성 실패: {e}", file=sys.stderr)
        try:
            teams.send_message(
                "❌ 스윙크루 Threads 리포트 실패",
                f"리포트 생성 중 오류 발생:\n\n`{e}`",
            )
        except Exception:
            pass
        raise


def _run_report(report_date=None):
    """리포트 생성 및 Teams 전송 실행."""
    if report_date:
        target = datetime.strptime(report_date, "%Y-%m-%d").date()
    else:
        target = date.today() - timedelta(days=1)

    since = target.isoformat()
    until = (target + timedelta(days=1)).isoformat()

    print(f"📊 {since} 리포트 생성 중...")

    # 해당 날짜 게시물 인사이트
    day_posts = threads.get_threads_with_insights(
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
    body = _build_report(since, day_posts, top_posts)

    print(body)
    print()

    # Teams 전송
    title = f"📊 SwingCrew 일간 리포트 ({since})"
    teams.send_message(title, body)
    print(f"✅ Teams 전송 완료")


def _build_report(report_date, day_posts, top_posts):
    """리포트 본문 생성 (Teams 플레인텍스트 호환)."""
    from datetime import datetime

    # 날짜 포맷: "3월 12일 (수)"
    DAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"]
    dt = datetime.strptime(report_date, "%Y-%m-%d")
    date_label = f"{dt.month}월 {dt.day}일 ({DAY_NAMES[dt.weekday()]})"

    sep = "─────────────────────────"
    sections = []

    # ── 헤더 ──
    sections.append(f"📊 SwingCrew 일간 리포트 | {date_label}\n{sep}")

    # ── 섹션 1: 오늘 성과 ──
    total_views = 0
    total_likes = 0
    total_replies = 0
    for p in day_posts:
        ins = p.get("insights", {})
        total_views += ins.get("views", 0)
        total_likes += ins.get("likes", 0)
        total_replies += ins.get("replies", 0)

    sections.append(
        f"📈 오늘 성과\n"
        f"  조회  {total_views:,}  (+{total_views:,})\n"
        f"  좋아요  {total_likes}  (+{total_likes})\n"
        f"  댓글  {total_replies}  (+{total_replies})"
    )

    # ── 섹션 2: 오늘 게시물 ──
    post_lines = ["✍️ 오늘 게시물"]
    if not day_posts:
        post_lines.append("  게시된 글이 없습니다.")
    else:
        medals = ["🥇", "🥈", "🥉"]
        ranked = sorted(
            day_posts,
            key=lambda p: p.get("insights", {}).get("views", 0),
            reverse=True,
        )
        for i, p in enumerate(ranked):
            ins = p.get("insights", {})
            views = ins.get("views", 0)
            likes = ins.get("likes", 0)
            replies = ins.get("replies", 0)
            text_preview = (p.get("text") or "")[:20].replace("\n", " ")
            medal = medals[i] if i < len(medals) else f" {i+1}."
            post_lines.append(f"  {medal} {text_preview}... 👁{views:,} ❤️{likes} 💬{replies}")
    sections.append("\n".join(post_lines))

    # ── 섹션 3: 누적 TOP 3 ──
    top_lines = ["🔥 누적 TOP 3"]
    if not top_posts:
        top_lines.append("  인사이트 데이터가 없습니다.")
    else:
        for i, p in enumerate(top_posts[:3], 1):
            ins = p.get("insights", {})
            views = ins.get("views", 0)
            text_preview = (p.get("text") or "")[:20].replace("\n", " ")
            top_lines.append(f"  {i}위 {text_preview}... 👁{views:,}")
    sections.append("\n".join(top_lines))

    # ── 섹션 4: 오늘의 인사이트 ──
    if day_posts:
        best = max(
            day_posts,
            key=lambda p: p.get("insights", {}).get("views", 0),
        )
        best_text = (best.get("text") or "")[:30].replace("\n", " ")
        sections.append(f"💡 오늘의 인사이트\n  → \"{best_text}\" 주제 조회율 최고")
    else:
        sections.append("💡 오늘의 인사이트\n  → 오늘 게시물 없음")

    sections.append(sep)

    # Teams(Power Automate)에서 \n이 무시되므로 <br>로 변환
    BR = "<br>"
    BR2 = "<br><br>"
    result = []
    for section in sections:
        result.append(section.replace("\n", BR))
    return BR2.join(result)
