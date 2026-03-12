"""MS Teams Power Automate Webhook 헬퍼 모듈"""

import os
import requests

MS_TEAMS_WEBHOOK_URL = os.getenv("MS_TEAMS_WEBHOOK_URL", "")


def _markdown_to_html(title, body):
    """리포트 마크다운을 Teams HTML로 변환."""
    import re

    html = f"<h2>{title}</h2>"
    for line in body.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            html += f"<h3>{line[3:]}</h3>"
        elif line.startswith("**") and line.endswith("**"):
            html += f"<p><b>{line[2:-2]}</b></p>"
        elif line.startswith("- **"):
            html += f"<p>{line[2:]}</p>"
        elif line.startswith("---"):
            html += "<hr>"
        elif line.startswith("**"):
            # **1.** text... 형태
            html += f"<p>{line}</p>"
        else:
            html += f"<p>{line}</p>"
    # 볼드 마크다운 → HTML
    html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html)
    return html


def send_message(title, body_markdown):
    """Power Automate Workflow 웹훅으로 Teams 채널에 메시지 전송.

    Args:
        title: 메시지 제목.
        body_markdown: 본문 (HTML).
    """
    if not MS_TEAMS_WEBHOOK_URL:
        raise ValueError("MS_TEAMS_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")

    # HTML 변환: 마크다운 → 간단한 HTML
    body_html = _markdown_to_html(title, body_markdown)

    payload = {
        "title": title,
        "body": body_html,
    }

    resp = requests.post(
        MS_TEAMS_WEBHOOK_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    resp.raise_for_status()
    return resp
