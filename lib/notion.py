"""노션 API 헬퍼 모듈"""

import os
import requests

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
NOTION_MANUSCRIPT_DB_ID = os.getenv("NOTION_MANUSCRIPT_DB_ID", "")

BASE_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


# ── DB 쿼리 ──────────────────────────────────────────────

def query_db(filter_payload=None, sorts=None, database_id=None):
    """노션 DB를 쿼리하여 페이지 목록 반환."""
    db_id = database_id or NOTION_DATABASE_ID
    url = f"{BASE_URL}/databases/{db_id}/query"
    body = {}
    if filter_payload:
        body["filter"] = filter_payload
    if sorts:
        body["sorts"] = sorts
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


# ── 페이지 생성 ──────────────────────────────────────────

def create_page(database_id, properties, content_text=""):
    """노션 DB에 새 페이지 생성.

    Args:
        database_id: 대상 DB ID.
        properties: 페이지 속성 dict.
        content_text: 본문 텍스트 (옵션). 줄바꿈으로 문단 분리.
    """
    url = f"{BASE_URL}/pages"
    body = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }
    if content_text:
        # 텍스트를 문단 블록으로 변환 (2000자 제한 대응)
        blocks = []
        for paragraph in content_text.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if paragraph == "---":
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            else:
                # 노션 rich_text는 블록당 최대 2000자
                chunks = [paragraph[i:i+2000] for i in range(0, len(paragraph), 2000)]
                rich_text = [{"type": "text", "text": {"content": chunk}} for chunk in chunks]
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": rich_text},
                })
        body["children"] = blocks

    resp = requests.post(url, headers=HEADERS, json=body)
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
    return {"select": {"name": value}}


def set_text(value):
    return {"rich_text": [{"type": "text", "text": {"content": value}}]}


def set_date(value):
    """value: ISO 형식 날짜 문자열 (예: 2026-03-12)"""
    return {"date": {"start": value}}


def set_url(value):
    return {"url": value}


def set_title(value):
    return {"title": [{"type": "text", "text": {"content": value}}]}


def set_select(value):
    return {"select": {"name": value}}


def set_relation(page_ids):
    """릴레이션 속성 payload 생성. page_ids: str 또는 list[str]."""
    if isinstance(page_ids, str):
        page_ids = [page_ids]
    return {"relation": [{"id": pid} for pid in page_ids]}
