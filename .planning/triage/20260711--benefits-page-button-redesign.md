---
date: 2026-07-11
type: fix
status: resolved
---

# Benefits 페이지 버튼 디자인 개선

## What
benefits/index.astro와 benefits/[category].astro의 버튼 및 헤더 디자인을 세련되게 재설계

## Why
기존 6개 카테고리 허브 버튼이 무지개 색상 그라디언트(indigo, pink, amber, gray, green, blue)로 이질감이 심했고, 내부 이모티콘도 투박했음. 탭 버튼도 이모티콘 포함 + benefit 브라운 계열 active 색상이 디자인 시스템과 부조화

## Files changed
- src/pages/benefits/index.astro — 허브 버튼(6개) 완전 재설계, 탭 버튼(5개) 이모티콘 제거 + navy active
- src/pages/benefits/[category].astro — 탭 버튼 이모티콘 제거 + navy active, 카테고리 헤더 h1 이모티콘 제거

## How
- **허브 버튼**: 흰색 카드 스타일(`--color-surface`) + 상단 3px 컬러 바 + 디자인 시스템 색상 매핑
  - youth: `--color-primary` (navy #1E3A5F)
  - child: `--color-primary-light` (lighter navy)
  - senior: `--color-accent` (amber #D97706)
  - general: `--color-muted` (gray #4B5563)
  - welfare: `--color-benefit` (warm brown #6B4226)
  - business: `--color-accent-dark` (darker amber #B45309)
- **탭 버튼**: 이모티콘 제거, active 상태를 `--color-primary` (navy) 로 통일
- **카테고리 헤더**: h1에서 이모티콘 제거

## Verification
- `npm run build` 성공 (23.6초, 에러 0)
- 디자인 토큰(`--color-primary`, `--color-accent`, `--color-benefit`, `--color-muted` 등) 100% 준수
- LSP 진단 없음 (Astro용 LSP 미설치이나 빌드 통과로 확인)