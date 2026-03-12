"""MS Teams Power Automate Webhook 헬퍼 모듈"""

import os
import re
import requests

MS_TEAMS_WEBHOOK_URL = os.getenv("MS_TEAMS_WEBHOOK_URL", "")


def send_message(title, body_markdown):
    """Power Automate Workflow 웹훅으로 Teams 채널에 메시지 전송.

    Args:
        title: 메시지 제목.
        body_markdown: 본문 (마크다운 → HTML 변환).
    """
    if not MS_TEAMS_WEBHOOK_URL:
        raise ValueError("MS_TEAMS_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")

    html_body = _markdown_to_html(body_markdown)
    html = f"<h2>{title}</h2>\n{html_body}"

    payload = {"text": html}

    resp = requests.post(
        MS_TEAMS_WEBHOOK_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    resp.raise_for_status()
    return resp


def _markdown_to_html(md):
    """간단한 마크다운 → HTML 변환."""
    lines = md.split("\n")
    html_lines = []

    for line in lines:
        # ## 헤딩
        if line.startswith("## "):
            html_lines.append(f"<h3>{line[3:]}</h3>")
        # ---  구분선
        elif line.strip() == "---":
            html_lines.append("<hr>")
        # - **항목** 리스트
        elif line.startswith("- "):
            content = line[2:]
            content = _inline_format(content)
            html_lines.append(f"<li>{content}</li>")
        # **N.** 번호 항목
        elif re.match(r"\*\*\d+\.\*\*", line):
            content = _inline_format(line)
            html_lines.append(f"<p>{content}</p>")
        # 빈 줄
        elif line.strip() == "":
            html_lines.append("")
        # 일반 텍스트
        else:
            content = _inline_format(line)
            html_lines.append(f"<p>{content}</p>")

    return "\n".join(html_lines)


def _inline_format(text):
    """인라인 마크다운 변환: **볼드**, [링크](url)."""
    # **bold**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # [text](url)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text
