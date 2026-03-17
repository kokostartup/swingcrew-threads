# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

스윙크루 Threads 자동 게시 플러그인 — 스윙크루 유튜브 원고를 Meta Threads 게시글로 변환하고 자동 게시하는 Python CLI + GitHub Actions 기반 시스템. 언어: 한국어.

## Commands

```bash
# 설치
pip install -r requirements.txt   # requests, python-dotenv

# CLI 실행
python swingcrew.py status                        # 노션 DB 현황 확인
python swingcrew.py publish [all|제목] [--limit N] # 승인된 글 Threads 게시
python swingcrew.py report                        # 전일 성과 리포트 → MS Teams 전송
python swingcrew.py report 2026-03-13             # 특정 날짜 리포트
```

테스트 프레임워크 없음. `.env` 파일에 환경변수 설정 필요. `publish`의 기본 limit=1 (명시하지 않으면 1건만 게시).

## Architecture

### Entry Point & CLI
- `swingcrew.py` — CLI 라우터. `status`, `publish`, `report` 3개 서브커맨드. 환경변수 검증 후 `commands/` 모듈로 위임.

### Commands (`commands/`)
- `threads_publish.py` — 노션에서 "승인" 상태 글 조회 → Threads API로 게시. 게시 타입별 분기: 숏폼/골프소식/영상코멘트는 단일 게시, 체인은 `---` 구분선으로 파트 분리 후 reply_to_id로 답글 연결, 롱폼(500자 초과)은 텍스트 첨부(text_attachment) 방식으로 게시 — "더 보기" 클릭으로 펼쳐 읽기.
- `threads_status.py` — DB 현황을 상태별(대기/승인/게시완료/실패)로 요약 출력.
- `threads_report.py` — 전일 게시물 인사이트 + TOP 10 인기 게시물 리포트를 Teams Adaptive Card로 전송.
- `commands/*.md` — Claude Code 슬래시 커맨드 정의 파일 (`/threads-publish`, `/threads-generate`, `/threads-news`, `/threads-video`, `/threads-image`, `/threads-check`).

### Lib (`lib/`)
- `notion.py` — Notion API 래퍼. DB 쿼리(`query_db`), 페이지 본문 읽기(`get_page_content`), 속성 읽기/쓰기 헬퍼. Notion-Version: 2022-06-28.
- `threads.py` — Threads Graph API 래퍼. 컨테이너 생성 → 30초 대기 → 발행 패턴. `post_text`, `post_text_with_attachment`, `post_image`, `post_chain` 편의 함수. 인사이트 조회(`get_media_insights`, `get_threads_with_insights`).
- `teams.py` — MS Teams Incoming Webhook으로 Adaptive Card 전송.

### Skills (`skills/`)
- `threads-post-generator/SKILL.md` — 슬래시 커맨드 라우터. 키워드에 따라 `/threads-generate`, `/threads-news`, `/threads-video` 등으로 분기.
- `threads-post-generator/references/style-guide.md` — 5가지 게시 타입별 스타일 가이드 (톤, 글자수, 구조, 예시 포함). 글 생성 시 반드시 참조.

### GitHub Actions (`.github/workflows/`)
- `threads_auto.yml` — 매일 5회(KST 7,12,17,20,22시) 승인된 글 1건씩 자동 게시. `workflow_dispatch`로 수동 실행 가능 (command, args, limit 파라미터).
- `threads_report.yml` — 매일 오전 8시 KST 전일 리포트 → Teams 전송. `workflow_dispatch`로 특정 날짜(YYYY-MM-DD) 지정 가능.

## Key Environment Variables

| 변수 | 용도 | 필요 커맨드 |
|------|------|-------------|
| `NOTION_TOKEN` | Notion API 토큰 | status, publish |
| `NOTION_DATABASE_ID` | Threads 게시글 DB ID | status, publish |
| `THREADS_ACCESS_TOKEN` | Meta Threads API 토큰 (60일 장기 토큰) | publish, report |
| `THREADS_USER_ID` | Threads 사용자 ID | publish, report |
| `THREADS_USERNAME` | Threads @username | publish, report |
| `MS_TEAMS_WEBHOOK_URL` | Teams 웹훅 URL | report |

## Notion DB Properties

게시 상태(select): 대기→승인→게시완료/실패. 게시 타입(select): 숏폼/롱폼/체인/골프소식/영상코멘트. 이미지 상태(select): 요청→생성중→완료/실패. 게시 순서(number): 승인 시 사용자가 직접 입력 (작은 숫자부터 먼저 게시). 기타: 제목, 게시일, Threads URL, 이미지(files), 메모.

## Important Patterns

- Threads API는 컨테이너 생성 후 **30초 대기** 필수 (`time.sleep(30)`) — API 제약.
- 체인 게시: 본문을 `---`(divider)로 파트 분리, 각 파트를 순차 게시하며 `reply_to_id`로 연결.
- 롱폼 게시: `text`에 첫 문단(500자 이내)을 넣고, `text_attachment={"plaintext": 전체본문}`으로 전달. Threads에서 "더 보기" 클릭 시 펼쳐 읽기. 텍스트 전용(이미지 불가), 첨부 최대 10,000자.
- `lib/notion.py`의 HEADERS는 모듈 로드 시 환경변수로 초기화됨 — `dotenv`가 먼저 로드되어야 함 (`swingcrew.py`에서 처리).
- `--limit`은 **성공 건수** 기준으로 동작. 롱폼 스킵/빈 본문 등은 카운트하지 않고 다음 글로 넘어감.
- 게시 순서: "게시 순서" 숫자 속성 오름차순 (작은 번호부터).
- 날짜/시간은 **KST(UTC+9)** 기준. GitHub Actions 러너는 UTC이므로 `datetime.now(KST)` 사용 (`threads_publish.py`의 `_now_kst_iso()`). `date.today()` 사용 금지 — UTC 기준이라 KST 자정 전후로 날짜가 어긋남.
- `THREADS_ACCESS_TOKEN`은 60일마다 갱신 필요. Meta 개발자 대시보드 > 앱 설정 > Threads API > 사용자 토큰 생성기에서 발급. GitHub Secrets도 함께 업데이트할 것.
