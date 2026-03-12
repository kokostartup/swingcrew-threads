"""Threads Graph API 헬퍼 모듈"""

import os
import time
import requests

THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN", "")
THREADS_USER_ID = os.getenv("THREADS_USER_ID", "")

BASE_URL = "https://graph.threads.net/v1.0"

API_TIMEOUT = 30  # 모든 API 호출 타임아웃 (초)
CONTAINER_WAIT_SEC = 30  # Threads 컨테이너 발행 대기 시간 (API 권장)


def _get_headers():
    """요청 시점의 토큰으로 헤더 생성."""
    token = os.getenv("THREADS_ACCESS_TOKEN", "") or THREADS_ACCESS_TOKEN
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def _get_token():
    """요청 시점의 액세스 토큰."""
    return os.getenv("THREADS_ACCESS_TOKEN", "") or THREADS_ACCESS_TOKEN


def _get_user_id():
    """요청 시점의 사용자 ID."""
    return os.getenv("THREADS_USER_ID", "") or THREADS_USER_ID


# ── 컨테이너 생성 ────────────────────────────────────────

def create_text_container(text, reply_to_id=None):
    """텍스트 미디어 컨테이너 생성 → creation_id 반환."""
    uid = _get_user_id()
    url = f"{BASE_URL}/{uid}/threads"
    data = {"media_type": "TEXT", "text": text}
    if reply_to_id:
        data["reply_to_id"] = reply_to_id
    resp = requests.post(url, headers=_get_headers(), data=data, timeout=API_TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("id")


def create_image_container(text, image_url, reply_to_id=None):
    """이미지 미디어 컨테이너 생성 → creation_id 반환."""
    uid = _get_user_id()
    url = f"{BASE_URL}/{uid}/threads"
    data = {
        "media_type": "IMAGE",
        "text": text,
        "image_url": image_url,
    }
    if reply_to_id:
        data["reply_to_id"] = reply_to_id
    resp = requests.post(url, headers=_get_headers(), data=data, timeout=API_TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("id")


# ── 발행 ─────────────────────────────────────────────────

def publish_container(creation_id):
    """미디어 컨테이너 발행 → post_id 반환."""
    uid = _get_user_id()
    url = f"{BASE_URL}/{uid}/threads_publish"
    data = {"creation_id": creation_id}
    resp = requests.post(url, headers=_get_headers(), data=data, timeout=API_TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("id")


# ── 편의 함수 ────────────────────────────────────────────

def post_text(text, reply_to_id=None):
    """텍스트 컨테이너 생성 → 30초 대기 → 발행 → post_id 반환."""
    creation_id = create_text_container(text, reply_to_id=reply_to_id)
    print(f"  컨테이너 생성 완료 (id: {creation_id}). {CONTAINER_WAIT_SEC}초 대기...")
    time.sleep(CONTAINER_WAIT_SEC)
    post_id = publish_container(creation_id)
    print(f"  게시 완료 (post_id: {post_id})")
    return post_id


def post_image(text, image_url):
    """이미지 포함 게시 → post_id 반환."""
    creation_id = create_image_container(text, image_url)
    print(f"  이미지 컨테이너 생성 완료 (id: {creation_id}). {CONTAINER_WAIT_SEC}초 대기...")
    time.sleep(CONTAINER_WAIT_SEC)
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
    """사용자 게시물 목록 조회."""
    uid = _get_user_id()
    url = f"{BASE_URL}/{uid}/threads"
    params = {
        "fields": "id,text,timestamp,permalink,media_type",
        "limit": limit,
        "access_token": _get_token(),
    }
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    resp = requests.get(url, params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("data", [])


def get_media_insights(media_id):
    """개별 게시물 인사이트 조회 → {views, likes, replies, reposts, quotes}."""
    url = f"{BASE_URL}/{media_id}/insights"
    params = {
        "metric": "views,likes,replies,reposts,quotes",
        "access_token": _get_token(),
    }
    resp = requests.get(url, params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    result = {}
    for item in data:
        try:
            result[item["name"]] = item["values"][0]["value"]
        except (KeyError, IndexError):
            result[item.get("name", "unknown")] = 0
    return result


def get_threads_with_insights(since=None, until=None, limit=25):
    """게시물 목록 + 각 게시물의 인사이트를 합쳐서 반환."""
    posts = get_user_threads(since=since, until=until, limit=limit)
    for post in posts:
        try:
            post["insights"] = get_media_insights(post["id"])
        except Exception as e:
            print(f"  ⚠️ 인사이트 조회 실패 (id={post.get('id')}): {e}")
            post["insights"] = {}
    return posts


# ── 키워드 검색 (threads_keyword_search 권한 필요) ────

def search_keyword(keyword, limit=25):
    """키워드로 공개 게시물 검색."""
    uid = _get_user_id()
    url = f"{BASE_URL}/{uid}/threads_search"
    params = {
        "q": keyword,
        "fields": "id,text,timestamp,permalink,username,media_type",
        "limit": limit,
        "access_token": _get_token(),
    }
    resp = requests.get(url, params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("data", [])


def search_keyword_with_views(keyword, limit=10):
    """키워드 검색 + 각 게시물 조회수 합산.

    Returns:
        tuple: (posts, total_views)
    """
    posts = search_keyword(keyword, limit=limit)
    total_views = 0
    for post in posts:
        try:
            post["insights"] = get_media_insights(post["id"])
            total_views += post["insights"].get("views", 0)
        except Exception as e:
            print(f"    ⚠️ 인사이트 실패 ({post.get('id')}): {e}")
            post["insights"] = {}
    return posts, total_views


def get_user_profile(username):
    """사용자의 공개 프로필 조회 (username 기반).

    Note: Threads API는 자기 자신의 프로필만 조회 가능.
          다른 사용자 프로필은 제한적.
    """
    uid = _get_user_id()
    url = f"{BASE_URL}/{uid}"
    params = {
        "fields": "id,username,name,threads_profile_picture_url,threads_biography",
        "access_token": _get_token(),
    }
    resp = requests.get(url, params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    return resp.json()
