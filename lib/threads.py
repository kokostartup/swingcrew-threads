"""Threads Graph API 헬퍼 모듈"""

import os
import time
import requests

THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN", "")
THREADS_USER_ID = os.getenv("THREADS_USER_ID", "")

BASE_URL = "https://graph.threads.net/v1.0"

HEADERS = {
    "Authorization": f"Bearer {THREADS_ACCESS_TOKEN}",
    "Content-Type": "application/x-www-form-urlencoded",
}


# ── 컨테이너 생성 ────────────────────────────────────────

def create_text_container(text, reply_to_id=None):
    """텍스트 미디어 컨테이너 생성 → creation_id 반환."""
    url = f"{BASE_URL}/{THREADS_USER_ID}/threads"
    data = {"media_type": "TEXT", "text": text}
    if reply_to_id:
        data["reply_to_id"] = reply_to_id
    resp = requests.post(url, headers=HEADERS, data=data)
    resp.raise_for_status()
    return resp.json().get("id")


def create_image_container(text, image_url, reply_to_id=None):
    """이미지 미디어 컨테이너 생성 → creation_id 반환."""
    url = f"{BASE_URL}/{THREADS_USER_ID}/threads"
    data = {
        "media_type": "IMAGE",
        "text": text,
        "image_url": image_url,
    }
    if reply_to_id:
        data["reply_to_id"] = reply_to_id
    resp = requests.post(url, headers=HEADERS, data=data)
    resp.raise_for_status()
    return resp.json().get("id")


# ── 발행 ─────────────────────────────────────────────────

def publish_container(creation_id):
    """미디어 컨테이너 발행 → post_id 반환."""
    url = f"{BASE_URL}/{THREADS_USER_ID}/threads_publish"
    data = {"creation_id": creation_id}
    resp = requests.post(url, headers=HEADERS, data=data)
    resp.raise_for_status()
    return resp.json().get("id")


# ── 편의 함수 ────────────────────────────────────────────

def post_text(text, reply_to_id=None):
    """텍스트 컨테이너 생성 → 30초 대기 → 발행 → post_id 반환."""
    creation_id = create_text_container(text, reply_to_id=reply_to_id)
    print(f"  컨테이너 생성 완료 (id: {creation_id}). 30초 대기...")
    time.sleep(30)
    post_id = publish_container(creation_id)
    print(f"  게시 완료 (post_id: {post_id})")
    return post_id


def post_image(text, image_url):
    """이미지 포함 게시 → post_id 반환."""
    creation_id = create_image_container(text, image_url)
    print(f"  이미지 컨테이너 생성 완료 (id: {creation_id}). 30초 대기...")
    time.sleep(30)
    post_id = publish_container(creation_id)
    print(f"  이미지 게시 완료 (post_id: {post_id})")
    return post_id


def post_chain(parts):
    """체인(글타래) 게시. parts: 텍스트 리스트. → post_id 리스트 반환."""
    post_ids = []

    # 첫 파트 게시
    print(f"  [1/{len(parts)}] 첫 파트 게시 중...")
    first_id = post_text(parts[0])
    post_ids.append(first_id)

    # 이후 파트: reply_to_id로 연결
    for i, part in enumerate(parts[1:], start=2):
        print(f"  [{i}/{len(parts)}] 답글 게시 중 (reply_to: {post_ids[-1]})...")
        pid = post_text(part, reply_to_id=post_ids[-1])
        post_ids.append(pid)

    return post_ids


def get_thread_url(post_id, username=None):
    """게시물 URL 생성."""
    uname = username or os.getenv("THREADS_USERNAME", "")
    return f"https://www.threads.net/@{uname}/post/{post_id}"


# ── 인사이트 / 분석 ─────────────────────────────────────

def get_user_threads(since=None, until=None, limit=25):
    """사용자 게시물 목록 조회.

    Args:
        since: ISO 8601 날짜 문자열 (예: "2026-03-11").
        until: ISO 8601 날짜 문자열 (예: "2026-03-12").
        limit: 조회 건수 (최대 100).

    Returns:
        게시물 리스트 [{id, text, timestamp, permalink, ...}, ...]
    """
    url = f"{BASE_URL}/{THREADS_USER_ID}/threads"
    params = {
        "fields": "id,text,timestamp,permalink,media_type",
        "limit": limit,
        "access_token": THREADS_ACCESS_TOKEN,
    }
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get("data", [])


def get_media_insights(media_id):
    """개별 게시물 인사이트 조회 → {views, likes, replies, reposts, quotes}.

    Returns:
        dict: 메트릭 이름 → 값 매핑.
    """
    url = f"{BASE_URL}/{media_id}/insights"
    params = {
        "metric": "views,likes,replies,reposts,quotes",
        "access_token": THREADS_ACCESS_TOKEN,
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return {item["name"]: item["values"][0]["value"] for item in data}


def get_threads_with_insights(since=None, until=None, limit=25):
    """게시물 목록 + 각 게시물의 인사이트를 합쳐서 반환.

    Returns:
        list[dict]: 각 항목에 id, text, timestamp, permalink, insights 포함.
    """
    posts = get_user_threads(since=since, until=until, limit=limit)
    for post in posts:
        try:
            post["insights"] = get_media_insights(post["id"])
        except Exception:
            post["insights"] = {}
    return posts
