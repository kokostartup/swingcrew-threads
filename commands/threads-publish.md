---
description: 노션에서 승인된 글을 Threads에 게시 (체인 포함)
argument-hint: [all 또는 특정 제목]
---

노션 "2026년 Threads 게시글" DB에서 "승인" 상태인 글을 찾아 Threads API로 게시한다.
게시 타입에 따라 다른 방식으로 게시한다.

## 실행 순서

1. 노션 DB(collection://bb743e71-955f-4909-9f44-2fd97cf58101)를 조회하여 게시 상태가 "승인"인 항목을 찾는다.
2. 승인된 항목이 없으면 "현재 승인 대기 중인 게시글이 없습니다" 안내.
3. 승인된 항목이 있으면 **게시 타입별로** 처리:

### 숏폼 / 롱폼 / 골프소식 / 영상코멘트 게시

a. 해당 페이지를 fetch하여 **페이지 본문(body)**에서 게시글 텍스트를 읽는다.
b. 이미지가 있는 경우(이미지 상태="완료") → media_type=IMAGE 사용
c. 이미지가 없는 경우 → media_type=TEXT 사용

**Step 1 — 미디어 컨테이너 생성:**
```bash
# 텍스트만
curl -X POST "https://graph.threads.net/v1.0/me/threads" \
  -H "Authorization: Bearer $THREADS_ACCESS_TOKEN" \
  -d "media_type=TEXT" \
  --data-urlencode "text=<게시글 내용>"

# 이미지 포함
curl -X POST "https://graph.threads.net/v1.0/me/threads" \
  -H "Authorization: Bearer $THREADS_ACCESS_TOKEN" \
  -d "media_type=IMAGE" \
  -d "image_url=<이미지URL>" \
  --data-urlencode "text=<게시글 내용>"
```

**Step 2 — 30초 대기 후 게시:**
```bash
curl -X POST "https://graph.threads.net/v1.0/me/threads_publish" \
  -H "Authorization: Bearer $THREADS_ACCESS_TOKEN" \
  -d "creation_id=<Step1에서 받은 ID>"
```

### 체인 게시 (스레드 체인)

a. 해당 페이지를 fetch하여 페이지 본문에서 구분선(---)으로 나뉜 각 파트를 추출한다.
b. **파트 1**을 일반 게시:
```bash
# Step 1: 미디어 컨테이너
curl -X POST "https://graph.threads.net/v1.0/me/threads" \
  -H "Authorization: Bearer $THREADS_ACCESS_TOKEN" \
  -d "media_type=TEXT" \
  --data-urlencode "text=<파트1 내용>"
# Step 2: 30초 대기 후 게시
curl -X POST "https://graph.threads.net/v1.0/me/threads_publish" \
  -H "Authorization: Bearer $THREADS_ACCESS_TOKEN" \
  -d "creation_id=<creation_id>"
```
c. publish 응답에서 **post_id** 획득
d. **파트 2 이후**는 `reply_to_id`로 답글 게시:
```bash
# Step 1: 답글 미디어 컨테이너
curl -X POST "https://graph.threads.net/v1.0/me/threads" \
  -H "Authorization: Bearer $THREADS_ACCESS_TOKEN" \
  -d "media_type=TEXT" \
  --data-urlencode "text=<파트N 내용>" \
  -d "reply_to_id=<이전 파트의 post_id>"
# Step 2: 30초 대기 후 게시
curl -X POST "https://graph.threads.net/v1.0/me/threads_publish" \
  -H "Authorization: Bearer $THREADS_ACCESS_TOKEN" \
  -d "creation_id=<creation_id>"
```
e. 각 파트 게시 사이에 30초 대기

### 게시 후 처리

성공 시:
- 노션 DB에서 "게시 상태"를 "게시완료"로 변경
- "게시일"을 오늘 날짜로 설정
- "Threads URL"에 첫 글 URL 저장 (https://www.threads.net/@swingcrew/post/<post_id>)

실패 시:
- "게시 상태"를 "실패"로 변경
- "메모"에 에러 메시지 기록

4. 모든 처리 완료 후 결과 요약을 사용자에게 보고한다.

## 환경 변수

- `THREADS_ACCESS_TOKEN`: Meta Developer에서 생성한 Threads API 액세스 토큰 (필수)
