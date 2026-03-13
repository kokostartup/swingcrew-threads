"""MS Teams Incoming Webhook 헬퍼 모듈"""

import os
import requests

MS_TEAMS_WEBHOOK_URL = os.getenv("MS_TEAMS_WEBHOOK_URL", "")


def send_message(title, body_markdown):
    """Adaptive Card 형식으로 Teams 채널에 메시지 전송.

    Args:
        title: 카드 제목.
        body_markdown: 본문 (마크다운).
    """
    if not MS_TEAMS_WEBHOOK_URL:
        raise ValueError("MS_TEAMS_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")

    payload = {
        "title": title,
        "body": body_markdown,
    }

    resp = requests.post(
        MS_TEAMS_WEBHOOK_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    resp.raise_for_status()
    return resp
