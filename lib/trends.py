"""실시간 인기 키워드 수집 모듈 (Google Trends RSS)"""

import xml.etree.ElementTree as ET
import requests

GOOGLE_TRENDS_RSS = "https://trends.google.co.kr/trending/rss?geo=KR"


def get_trending_keywords(limit=10):
    """Google Trends 한국 일간 인기 검색어를 가져온다.

    Args:
        limit: 가져올 키워드 수 (기본 10).

    Returns:
        list[str]: 인기 키워드 리스트.
    """
    resp = requests.get(GOOGLE_TRENDS_RSS, timeout=15)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    items = root.findall(".//item")

    keywords = []
    for item in items[:limit]:
        title = item.find("title")
        if title is not None and title.text:
            keywords.append(title.text.strip())

    return keywords
