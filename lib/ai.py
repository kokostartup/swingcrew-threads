"""Claude API 콘텐츠 생성 헬퍼 모듈"""

import os
import json
import requests

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = "claude-opus-4-5-20250514"
API_URL = "https://api.anthropic.com/v1/messages"

# ── 스타일 가이드 ────────────────────────────────────────

STYLE_GUIDE = """
# Threads 글 스타일 가이드

## 톤 & 보이스
- 기본 톤: "옆자리 싱글 골퍼 형이 알려주는 느낌"
- 반말 사용 (단, 비하/조롱 X)
- 전문 용어는 쉽게 풀어서
- "~했거든" "~인 거 알아?" "~해봐" 같은 구어체
- 이모지 적절히 사용 (1~3개, 과하지 않게)

## 피해야 할 것
- 딱딱한 존댓말 ("~입니다", "~하십시오")
- 과도한 이모지 도배
- 너무 긴 문장
- 전문 용어만 나열
- 광고성 멘트 ("지금 바로!", "놓치지 마세요!")

## 훅(첫 줄) 패턴
1. 반전형: "프로들이 절대 안 알려주는 비밀 하나"
2. 질문형: "드라이버 200야드도 안 나가는 진짜 이유 알아?"
3. 숫자형: "3개월 만에 핸디캡 10 줄인 방법"
4. 공감형: "연습장에서는 잘 치는데 필드만 가면 망하는 사람?"
5. 충격형: "지금 너 스윙 10번 중 8번은 틀렸어"

## 피해야 할 훅
- "안녕하세요~" 로 시작
- "오늘은 ~에 대해 이야기해볼게요"
- 너무 긴 서론

## CTA 패턴 (자연스럽게)
- "다음에 연습장 가면 한번 해봐"
- "이거 저장해두고 필드 가기 전에 봐"
- "궁금한 거 있으면 댓글 남겨"
- "같은 고민 있는 친구한테 공유해줘"
""".strip()


# ── Claude API 호출 ──────────────────────────────────────

def call_claude(system_prompt, user_prompt, max_tokens=4000):
    """Claude Messages API 호출 → 텍스트 반환."""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    resp = requests.post(API_URL, headers=headers, json=body)
    resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"]


def _parse_json(text):
    """Claude 응답에서 JSON 추출. 코드블록 안에 있을 수 있음."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # 첫 줄 (```json) 제거
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


# ── 콘텐츠 생성 함수 ─────────────────────────────────────

def generate_shortform(manuscript_text, title, count=7):
    """숏폼 게시글 생성 → JSON 배열 반환.

    Returns: [{"hook": "...", "text": "..."}, ...]
    """
    system = f"""{STYLE_GUIDE}

## 작업
아래 원고를 기반으로 숏폼 Threads 게시글을 {count}개 생성해.
각 게시글은 서로 다른 각도/관점, 서로 다른 훅(첫 줄)을 사용해야 해.

규칙:
- 각 게시글 500자 이내
- 다양한 템플릿 사용 (꿀팁형, 스토리형, 리스트형, 질문형)
- JSON 배열로 반환: [{{"hook": "첫줄", "text": "전체 게시글 텍스트"}}]
- JSON만 반환하고, 다른 설명은 쓰지 마"""

    user = f"원고 제목: {title}\n\n원고 내용:\n{manuscript_text}"
    result = call_claude(system, user, max_tokens=8000)
    return _parse_json(result)


def generate_longform(manuscript_text, title):
    """롱폼 에세이 생성 → {"hook": "...", "text": "..."} 반환."""
    system = f"""{STYLE_GUIDE}

## 작업
아래 원고를 기반으로 롱폼 에세이 Threads 게시글 1개를 생성해.

규칙:
- 1,500~3,000자
- 구조: 강력한 훅 → 공감 유도 → 스토리텔링 본론 → 실천 메시지 결론
- 숏폼보다 약간 정중한 반말 ("~거든요", "~더라고요")
- 소제목은 [] 로 감싸기 (볼드체 미지원)
- JSON으로 반환: {{"hook": "첫줄", "text": "전체 에세이 텍스트"}}
- JSON만 반환하고, 다른 설명은 쓰지 마"""

    user = f"원고 제목: {title}\n\n원고 내용:\n{manuscript_text}"
    result = call_claude(system, user, max_tokens=8000)
    return _parse_json(result)


def generate_chain(manuscript_text, title, parts=3):
    """체인(글타래) 생성 → 파트 목록 반환.

    Returns: [{"part": 1, "text": "..."}, ...]
    """
    system = f"""{STYLE_GUIDE}

## 작업
아래 원고를 기반으로 {parts}파트짜리 체인(글타래) Threads 게시글 1세트를 생성해.

규칙:
- 각 파트 200~400자
- 파트 끝에 "1/{parts}", "2/{parts}" 번호 표기
- 첫 파트: 훅 + 문제 제기 (클릭 유도)
- 중간 파트: 핵심 설명
- 마지막 파트: 결론 + CTA
- JSON 배열로 반환: [{{"part": 1, "text": "파트1 전체 텍스트"}}]
- JSON만 반환하고, 다른 설명은 쓰지 마"""

    user = f"원고 제목: {title}\n\n원고 내용:\n{manuscript_text}"
    result = call_claude(system, user, max_tokens=4000)
    return _parse_json(result)


def generate_news_posts(topic=None, count=4):
    """골프 뉴스 게시글 생성 → JSON 배열 반환.

    Returns: [{"hook": "...", "text": "..."}, ...]
    """
    system = f"""{STYLE_GUIDE}

## 작업
최신 골프 소식을 바탕으로 Threads 게시글을 {count}개 생성해.
너의 지식을 활용하여 최근 골프계 주요 뉴스/트렌드를 다뤄.

규칙:
- 각 게시글 200~500자
- 아마추어 골퍼에게 흥미로운 소식 위주
- 구조: 속보/소식 한 줄 요약 → 상세 2~3문장 → 스윙크루 코멘트 → 이모지
- "~래" "~라고 하네" 같은 전달 어투 가능
- PGA Tour, KPGA, LPGA, 장비 소식 등
- JSON 배열로 반환: [{{"hook": "첫줄", "text": "전체 게시글 텍스트"}}]
- JSON만 반환하고, 다른 설명은 쓰지 마"""

    user_msg = "최신 골프 뉴스를 바탕으로 게시글을 생성해줘."
    if topic:
        user_msg = f"주제: {topic}\n\n이 주제와 관련된 골프 소식 게시글을 생성해줘."
    result = call_claude(system, user_msg, max_tokens=4000)
    return _parse_json(result)


def generate_video_comment(video_title, video_url, manuscript_text=""):
    """영상 코멘트 게시글 생성 → {"text": "..."} 반환."""
    system = f"""{STYLE_GUIDE}

## 작업
스윙크루 유튜브 영상을 홍보하는 Threads 게시글 1개를 생성해.

규칙:
- 150~300자
- 영상 핵심 내용을 훅으로 (호기심 유발)
- "이번 영상에서는~" 같은 딱딱한 시작 X
- 가장 충격적/유용한 포인트를 훅으로
- 영상 링크 포함
- 마지막에 "🔗 스윙크루" 추가
- JSON으로 반환: {{"text": "전체 게시글 텍스트"}}
- JSON만 반환하고, 다른 설명은 쓰지 마"""

    user = f"영상 제목: {video_title}\n영상 URL: {video_url}"
    if manuscript_text:
        user += f"\n\n관련 원고:\n{manuscript_text}"
    result = call_claude(system, user, max_tokens=2000)
    return _parse_json(result)


def generate_image_prompt(post_text):
    """게시글 텍스트에서 이미지 생성용 프롬프트 생성."""
    system = """당신은 소셜 미디어 이미지 프롬프트 전문가입니다.
아래 골프 관련 게시글에 어울리는 이미지를 만들기 위한 영어 프롬프트를 생성해주세요.

규칙:
- 정사각형 (1:1) 비율
- 깔끔한 일러스트 스타일
- 골프 테마
- 텍스트 없이 이미지만
- 프롬프트만 반환 (설명 X)"""

    result = call_claude(system, f"게시글:\n{post_text}", max_tokens=500)
    return result.strip()
