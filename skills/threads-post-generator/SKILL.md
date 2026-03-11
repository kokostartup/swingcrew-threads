---
name: threads-post-generator
description: >
  스윙크루 유튜브 원고를 Meta Threads 게시글로 변환하는 스킬.
  "쓰레드 글 만들어", "Threads 게시글 생성", "원고를 쓰레드용으로",
  "SNS 글 만들어", "쓰레드 변환", "threads post" 등의 요청에 사용한다.
  노션에서 원고를 읽고 5가지 타입(숏폼/롱폼/체인/골프소식/영상코멘트)의
  Threads 게시글을 생성하여 노션 DB에 저장한다.
version: 0.2.1
---

# Threads 게시글 스킬 — 커맨드 라우터

이 스킬은 커맨드별로 동작한다. 각 커맨드 파일에 상세 프로세스가 정의되어 있으므로 이 파일에서는 반복하지 않는다.

## 커맨드 목록

| 커맨드 | 용도 |
|--------|------|
| /threads-generate | 원고 → 숏폼·롱폼·체인 게시글 생성 |
| /threads-news | 최신 골프 소식 게시글 생성 |
| /threads-video | 유튜브 영상 코멘트 게시글 생성 |
| /threads-publish | 승인된 글을 Threads API로 게시 |
| /threads-check | DB 현황 요약 |
| /threads-image | 이미지 생성 (Gemini 웹) |

## 공통 리소스

- **노션 DB**: collection://bb743e71-955f-4909-9f44-2fd97cf58101
- **스타일 가이드**: `references/style-guide.md` — 글 생성 커맨드(/threads-generate, /threads-news, /threads-video) 실행 시에만 참조할 것. 게시(/threads-publish), 현황 확인(/threads-check), 이미지 생성(/threads-image) 시에는 불필요.
