# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

스윙크루 Threads 자동 게시 시스템 — 노션 DB에서 콘텐츠를 관리하고, Claude API로 게시글을 생성하며, Threads Graph API로 자동 게시하는 Python CLI 도구.

## Commands

```bash
python swingcrew.py status                         # 노션 DB 현황 확인
python swingcrew.py generate [키워드]              # 원고 → 숏폼/롱폼/체인 생성
python swingcrew.py news [키워드]                  # 골프소식 게시글 생성
python swingcrew.py video <URL 또는 제목>          # 영상코멘트 생성
python swingcrew.py publish [all|제목] [--limit N] # 승인된 글 Threads 게시
python swingcrew.py report                         # 전일 성과 리포트 → Teams 전송

pip install requests python-dotenv                 # 의존성 설치
```

## Architecture

```
swingcrew.py          CLI 진입점 — sys.argv 파싱, 환경변수 검증, 커맨드 분기
lib/
  notion.py           노션 API 헬퍼 (query_db, create_page, update_page, 속성 읽기/쓰기)
  threads.py          Threads Graph API (컨테이너 생성 → 발행, 체인 게시, 인사이트 조회)
  ai.py               Claude API 콘텐츠 생성 (숏폼/롱폼/체인/뉴스/영상코멘트)
  teams.py            MS Teams 웹훅 메시지 전송
  trends.py           Google Trends RSS 인기 키워드 수집
commands/
  threads_status.py   노션 DB 상태별 카운트 출력
  threads_generate.py 원고 기반 게시글 대량 생성 (숏폼 7개 + 롱폼 1개 + 체인 1세트)
  threads_news.py     Claude로 골프소식 게시글 생성
  threads_video.py    유튜브 영상 코멘트 생성 (승인 상태로 즉시 게시 가능)
  threads_publish.py  승인된 게시글을 Threads에 게시 (체인은 reply_to_id 연결)
  threads_report.py   전일 성과 + 트렌드 분석 리포트 → Teams 전송
```

## Key Workflows

- **콘텐츠 생성 흐름**: 원고 DB → Claude API → 노션 게시글 DB (상태: "대기")
- **게시 흐름**: 노션에서 "승인" → `publish` 명령 → Threads API → 노션 "게시완료" + URL 기록
- **자동 게시**: GitHub Actions가 하루 5회 스케줄로 `publish all --limit 1` 실행
- **Threads 컨테이너 발행**: 생성 후 30초 대기 필수 (API 권장)

## Environment Variables

`.env` 파일에 설정 (`.gitignore`에 포함됨):
- `NOTION_TOKEN`, `NOTION_DATABASE_ID` — 게시글 DB
- `NOTION_MANUSCRIPT_DB_ID` — 원고 DB
- `THREADS_ACCESS_TOKEN`, `THREADS_USER_ID`, `THREADS_USERNAME`
- `ANTHROPIC_API_KEY` — Claude API
- `MS_TEAMS_WEBHOOK_URL` — Teams 리포트 전송

## Spec Files

`commands/*.md` — 각 커맨드의 상세 사양 (레퍼런스 문서)
`skills/threads-post-generator/references/style-guide.md` — 게시글 스타일 가이드
