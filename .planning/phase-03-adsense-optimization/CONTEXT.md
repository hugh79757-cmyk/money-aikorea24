# CONTEXT.md — Phase 03: AdSense Revenue Optimization

## Problem Statement
현재 자동광고(Auto Ads) + 동일 슬롯 ID(`8107272066`) 수동 광고 3개만 배치.
RPM 최적화를 위해 본문 중간 in-article 광고, PC 리더보드, 모바일 스티키 추가 필요.
IntersectionObserver 기반 레이지로드로 CLS 방지 + 광고 효율 극대화.

## Current State
- **Auto Ads**: `BaseHead.astro:66`에서 로드 (전체 페이지)
- **수동 광고**: `BlogPost.astro`에 3개 (상단/중간/하단), 모두 동일 슬롯 `8107272066`
- ** publisher ID**: `ca-pub-5938862195544185` (12곳 하드코딩)
- **CSS**: `global.css:22-27`에 `ins.adsbygoogle` 공통 정렬만 존재
- **다크모드**: `data-theme` 속성 기반 (`dark` 클래스 아님)

## Decisions

### D1: 광고 단위 전략
- **자동광고**: 유지 (건드리지 않음)
- **수동 in-article**: 본문 중간에 반응형 fluid 광고 (WordCount에 따라 0~3개)
- **리더보드**: PC 전용 728x90, 본문 끝
- **모바일 스티키**: 모바일 전용 320x50, 하단 고정, 닫기 버튼 포함
- **슬롯 ID**: 기존 `8107272066` 재사용 (동일 슬롯으로 다중 배치)

### D2: 레이지로드 전략
- IntersectionObserver로 `ins.lazyad` 관찰
- `rootMargin: "400px 0px"` (미리 로드)
- 초기화 후 `data-adsbygoogle-status="done"` 속성 부여
- 자동광고와 충돌 방지: 이미 초기화된 ins는 건너뛰기

### D3: 조건부 배치
- WordCount < 800: 본문 중간 광고 0개 (리더보드 + 스티키만)
- WordCount >= 800 + 고단가 카테고리(insurance, finance, loan, tax, invest): in-article 3개
- 그 외: in-article 2개

### D4: 마커 기반 삽입
- `.Content`를 자르지 않고 `replace` 함수로 마커 주입 → partial 치환
- `<!--AD1-->`, `<!--AD2-->`, `<!--AD3-->` 마커 사용

## Scope

### In Scope
1. `src/components/adsense/` 파셜 3종 생성 (in-article, leaderboard, mobile-sticky)
2. `BlogPost.astro` 마커 기반 광고 삽입 로직
3. `BaseHead.astro` IntersectionObserver 글로벌 스크립트
4. `global.css` 광고 관련 스타일 + 다크모드 대응
5. `consts.ts`에 `ADSENSE_CLIENT` 상수 추가

### Out of Scope
- AdSense 콘솔 설정 (슬롯 ID 발급은 사용자 몫)
- 자동광고 설정 변경
- 수익 분석/리포팅

## Technical Context

### 수정 대상 파일
| 파일 | 변경 |
|------|------|
| `src/consts.ts` | `ADSENSE_CLIENT` 상수 추가 |
| `src/components/adsense/in-article.html` | **신규** — 본문 중간 반응형 광고 |
| `src/components/adsense/leaderboard.html` | **신규** — PC 728x90 리더보드 |
| `src/components/adsense/mobile-sticky.html` | **신규** — 모바일 하단 스티키 + 닫기 |
| `src/layouts/BlogPost.astro` | 마커 기반 광고 삽입 + 조건부 분기 |
| `src/components/BaseHead.astro` | IntersectionObserver 스크립트 |
| `src/styles/global.css` | 광고 스타일 + 다크모드 + 반응형 |
