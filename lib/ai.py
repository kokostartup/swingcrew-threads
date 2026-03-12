"""Claude API 콘텐츠 생성 모듈"""

import os
import json
import requests

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"
API_URL = "https://api.anthropic.com/v1/messages"

STYLE_GUIDE = """
# 스윙크루 Threads 스타일 가이드

## 톤: "옆자리 싱글 골퍼 형이 알려주는 느낌"
- 반말 사용 (비하/조롱 X)
- 전문 용어는 쉽게 풀어서
- "~했거든" "~인 거 알아?" "~해봐" 같은 구어체
- 이모지 적절히 사용 (과하지 않게, 1~3개)

## 피해야 할 것
- 딱딱한 존댓말 ("~입니다", "~하십시오")
- 과도한 이모지 도배
- 너무 긴 문장, 전문 용어만 나열
- 광고성 멘트 ("지금 바로!", "놓치지 마세요!")

## 훅(첫 줄) 공식
1. 반전형: "프로들이 절대 안 알려주는 비밀 하나"
2. 질문형: "드라이버 200야드도 안 나가는 진짜 이유 알아?"
3. 숫자형: "3개월 만에 핸디캡 10 줄인 방법"
4. 공감형: "연습장에서는 잘 치는데 필드만 가면 망하는 사람?"
5. 충격형: "지금 너 스윙 10번 중 8번은 틀렸어"

## CTA 패턴 (자연스럽게)
- "다음에 연습장 가면 한번 해봐"
- "이거 저장해두고 필드 가기 전에 봐"
- "궁금한 거 있으면 댓글 남겨"
"""


def call_claude(system_prompt, user_prompt, max_tokens=4000):
    """Claude Messages API 호출 → 텍스트 반환."""
    key = os.getenv("ANTHROPIC_API_KEY", "") or ANTHROPIC_API_KEY
    if not key:
        raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")

    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"]


def _parse_json(text):
    """Claude 응답에서 JSON 추출."""
    # ```json ... ``` 블록이 있으면 추출
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return json.loads(text.strip())


def generate_shortform(manuscript_text, title, count=7):
    """숏폼 게시글 생성 → list[dict] with keys: title, text"""
    system = STYLE_GUIDE + """
너는 스윙크루의 Threads 콘텐츠 작성자야.
원고를 분석해서 다양한 각도로 숏폼 게시글을 만들어.

각 게시글은:
- 200~500자
- 서로 다른 각도/관점, 서로 다른 훅(첫 줄)
- 템플릿: 꿀팁형, 스토리형, 리스트형, 질문형을 골고루

JSON 배열로 응답해. 각 항목: {"title": "간략 주제", "text": "게시글 본문"}
"""
    prompt = f"""원고 제목: {title}

원고 내용:
{manuscript_text}

위 원고를 분석하여 {count}개의 숏폼 게시글을 만들어줘.
각각 다른 각도, 다른 훅을 사용해야 해.
JSON 배열로만 응답해."""

    result = call_claude(system, prompt, max_tokens=6000)
    return _parse_json(result)


def generate_longform(manuscript_text, title):
    """롱폼 에세이 생성 → dict with keys: hook, text"""
    system = STYLE_GUIDE + """
너는 스윙크루의 Threads 콘텐츠 작성자야.
원고를 1,500~3,000자 에세이로 재구성해.

구조:
- 강력한 훅 (1~2줄)
- 공감 유도 (독자 고민 짚기)
- 본론 (원고 핵심을 스토리로)
- 결론 (실천 가능한 메시지)

톤: 약간 정중한 반말 ("~거든요", "~더라고요")
소제목은 [] 또는 <>로 감싸기 (Threads 볼드체 미지원)

JSON으로 응답: {"hook": "첫 줄 훅", "text": "전체 에세이 본문"}
"""
    prompt = f"""원고 제목: {title}

원고 내용:
{manuscript_text}

위 원고를 바탕으로 롱폼 에세이를 작성해줘.
1,500~3,000자 분량으로.
JSON으로만 응답해."""

    result = call_claude(system, prompt, max_tokens=6000)
    return _parse_json(result)


def generate_chain(manuscript_text, title, parts=3):
    """체인(글타래) 생성 → list[str] (각 파트 텍스트)"""
    system = STYLE_GUIDE + """
너는 스윙크루의 Threads 콘텐츠 작성자야.
원고를 연결 글타래(체인)로 만들어.

규칙:
- 각 파트 200~400자
- 파트 끝에 "1/n", "2/n" 번호 표기
- 첫 파트: 훅 + 문제 제기 (클릭 유도)
- 중간 파트: 핵심 설명
- 마지막 파트: 결론 + CTA

JSON 배열로 응답: ["파트1 텍스트", "파트2 텍스트", ...]
"""
    prompt = f"""원고 제목: {title}

원고 내용:
{manuscript_text}

위 원고를 {parts}파트 체인으로 만들어줘.
JSON 문자열 배열로만 응답해."""

    result = call_claude(system, prompt, max_tokens=4000)
    return _parse_json(result)


def generate_news_posts(news_text, count=4):
    """골프소식 게시글 생성 → list[dict] with keys: title, text"""
    system = STYLE_GUIDE + """
너는 스윙크루의 Threads 콘텐츠 작성자야.
최신 골프 소식을 아마추어 골퍼 관점에서 게시글로 작성해.

각 게시글 구조:
- 속보/소식 한 줄 요약 (훅)
- 상세 내용 2~3문장
- 스윙크루 관점 코멘트 1~2문장
- 관련 이모지

톤: 기본 톤 유지하되 뉴스 전달이므로 약간 객관적
"~래" "~라고 하네" 같은 전달 어투 가능
200~500자

JSON 배열로 응답: [{"title": "소식 키워드", "text": "게시글 본문"}, ...]
"""
    prompt = f"""다음 골프 관련 소식/정보를 바탕으로 {count}개의 Threads 게시글을 만들어줘.

소식/주제:
{news_text}

아마추어 골퍼에게 흥미로운 내용 위주로.
JSON 배열로만 응답해."""

    result = call_claude(system, prompt, max_tokens=4000)
    return _parse_json(result)


def generate_video_comment(video_title, video_url, manuscript_text=""):
    """영상코멘트 게시글 생성 → str (게시글 본문)"""
    system = STYLE_GUIDE + """
너는 스윙크루의 Threads 콘텐츠 작성자야.
유튜브 영상을 소개하는 짧은 코멘트 게시글을 만들어.

구조:
- 영상 핵심 내용을 훅으로 (호기심 유발)
- 왜 봐야 하는지 1~2문장
- 영상 링크
- 🔗 스윙크루

톤:
- "이번 영상에서는~" 같은 딱딱한 시작 X
- 영상 내용에서 가장 충격적/유용한 포인트를 훅으로
- 150~300자

게시글 본문 텍스트만 응답해 (JSON 아님).
"""
    prompt = f"""영상 제목: {video_title}
영상 URL: {video_url}
"""
    if manuscript_text:
        prompt += f"""
관련 원고 내용:
{manuscript_text}
"""
    prompt += """
위 영상에 대한 Threads 코멘트 게시글을 작성해줘.
영상 URL을 본문에 포함해야 해.
텍스트만 응답해."""

    return call_claude(system, prompt, max_tokens=1000)


def generate_image_prompt(post_text):
    """게시글에 맞는 이미지 생성 프롬프트 → str"""
    system = "You are an expert at creating image generation prompts for golf-related social media posts."
    prompt = f"""다음 Threads 게시글에 어울리는 이미지를 생성하기 위한 영문 프롬프트를 작성해줘.

게시글:
{post_text}

간결하고 구체적인 영문 이미지 프롬프트만 응답해."""

    return call_claude(system, prompt, max_tokens=500)
