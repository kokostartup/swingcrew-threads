# 스윙크루 Threads 자동 게시 플러그인

스윙크루 유튜브 원고를 Meta Threads 게시글로 자동 변환하고 게시하는 플러그인입니다.

## 게시글 5가지 타입

| 타입 | 설명 | 커맨드 |
|------|------|--------|
| 숏폼 | 짧은 팁/훅 (200~500자) | `/threads-generate` |
| 롱폼 | 에세이 스토리텔링 (1,500~3,000자) | `/threads-generate` |
| 체인 | 연결 글타래 3~5파트 (답글 형식) | `/threads-generate` |
| 골프소식 | 최신 골프 뉴스/트렌드 | `/threads-news` |
| 영상코멘트 | 유튜브 영상 홍보 + 링크 | `/threads-video` |

## 커맨드

- `/threads-generate [키워드]`: 원고에서 숏폼+롱폼+체인 한번에 생성 → 노션 자동 저장
- `/threads-news [키워드]`: 웹 검색으로 골프 소식 게시글 생성
- `/threads-video [URL]`: 유튜브 영상 코멘트 게시글 생성
- `/threads-publish [all]`: 승인된 글을 Threads에 게시 (체인은 자동 답글 연결)
- `/threads-image [all]`: 이미지 요청된 글에 Gemini 웹으로 이미지 생성
- `/threads-check`: 게시글 DB 현황 확인

## 스케줄 태스크

- **threads-auto-publish**: 매일 5회 (8시, 11시, 14시, 18시, 21시) — 승인된 글 자동 게시
- **threads-image-gen**: 매일 낮 12시 — 이미지 자동 생성

## 사용 흐름

1. `/threads-generate` 로 원고 → 숏폼+롱폼+체인 한번에 생성 → 노션 자동 저장
2. `/threads-news` 로 골프 소식 게시글 생성
3. `/threads-video` 로 영상 업로드 시 코멘트 생성
4. 노션에서 글 확인 후 **"게시 승인" 버튼 클릭**
5. 이미지 필요한 글에 **"이미지 생성" 버튼 클릭**
6. 하루 5회 자동 게시 (또는 `/threads-publish`로 수동)
7. `/threads-check` 로 현황 확인

## 노션 DB 버튼
- **게시 승인**: 클릭 시 게시 상태 → "승인"
- **이미지 생성**: 클릭 시 이미지 상태 → "요청"
