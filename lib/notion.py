"""노션 API 헬퍼 모듈"""

import os
import requests

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

BASE_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


# ── DB 쿼리 ──────────────────────────────────────────────

def query_db(filter_payload=None, database_id=None):
    """노션 DB를 쿼리하여 페이지 목록 반환."""
    db_id = database_id or NOTION_DATABASE_ID
    url = f"{BASE_URL}/databases/{db_id}/query"
    body = {}
    if filter_payload:
        body["filter"] = filter_payload
    resp = requests.post(url, headers=HEADERS, json=body)
    resp.raise_for_status()
    return resp.json().get("results", [])


# ── 페이지 조회 ──────────────────────────────────────────

def get_page_content(page_id):
    """페이지 본문 블록을 텍스트로 변환."""
    url = f"{BASE_URL}/blocks/{page_id}/children?page_size=100"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    blocks = resp.json().get("results", [])

    lines = []
    for block in blocks:
        btype = block.get("type", "")
        data = block.get(btype, {})
        rich_texts = data.get("rich_text", [])
        text = "".join(rt.get("plain_text", "") for rt in rich_texts)
        if btype == "divider":
            lines.append("---")
        elif text:
            lines.append(text)
    return "\n\n".join(lines)


# ── 페이지 업데이트 ──────────────────────────────────────

def update_page(page_id, properties):
    """페이지 속성 업데이트."""
    url = f"{BASE_URL}/pages/{page_id}"
    resp = requests.patch(url, headers=HEADERS, json={"properties": properties})
    resp.raise_for_status()
    return resp.json()


# ── 속성 읽기 헬퍼 ────────────────────────────────────────

def get_prop_text(page, prop_name):
    """title 또는 rich_text 속성에서 문자열 추출."""
    prop = page.get("properties", {}).get(prop_name, {})
    ptype = prop.get("type", "")
    if ptype == "title":
        parts = prop.get("title", [])
    elif ptype == "rich_text":
        parts = prop.get("rich_text", [])
    else:
        return ""
    return "".join(p.get("plain_text", "") for p in parts)


def get_prop_select(page, prop_name):
    """select 속성에서 이름 추출."""
    prop = page.get("properties", {}).get(prop_name, {})
    ptype = prop.get("type", "")
    if ptype == "select":
        sel = prop.get("select")
        return sel.get("name", "") if sel else ""
    if ptype == "status":
        sel = prop.get("status")
        return sel.get("name", "") if sel else ""
    return ""


def get_prop_files(page, prop_name):
    """files 속성에서 첫 번째 파일 URL 추출."""
    prop = page.get("properties", {}).get(prop_name, {})
    files = prop.get("files", [])
    if not files:
        return ""
    f = files[0]
    if f.get("type") == "external":
        return f.get("external", {}).get("url", "")
    if f.get("type") == "file":
        return f.get("file", {}).get("url", "")
    return ""


# ── 속성 쓰기 헬퍼 ────────────────────────────────────────

def set_status(value):
    return {"status": {"name": value}}


def set_text(value):
    return {"rich_text": [{"type": "text", "text": {"content": value}}]}


def set_date(value):
    """value: ISO 형식 날짜 문자열 (예: 2026-03-12)"""
    return {"date": {"start": value}}


def set_url(value):
    return {"url": value}
