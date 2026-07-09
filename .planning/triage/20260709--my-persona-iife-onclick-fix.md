---
date: 2026-07-09
type: fix
status: resolved
---

# my-persona 버튼 onclick 수정 + 배포

## What
- `my-persona.astro` 페이지 버튼 클릭이 Production에서 동작하지 않는 문제 수정
- `/benefits/` 혜택 허브 페이지, 모바일 햄버거 메뉴, 썸네일 가운데 정렬 배포
- Cloudflare 인증을 제한된 API Token에서 Global API Key로 전환

## Why
- commit `7ebe34d`에서 Astro `define:vars`를 추가했는데, 이게 `<script is:inline>`을 IIFE로 감싸서 `onclick="startStep()"` 같은 inline 핸들러가 전역 함수를 찾지 못함
- 기존 `CLOUDFLARE_API_TOKEN`이 `Pages Read` 권한만 있어 wrangler 배포 불가

## Files changed
- `src/pages/my-persona.astro` — IIFE 안 함수들을 `window.*`로 노출 (startStep, goStep, selectOption, selectProvince, resetForm, shareKakao, shareTwitter, copyUrl, downloadCard, toggleDetail, toggleStory)
- `src/pages/benefits/index.astro` — 혜택 카테고리 허브
- `src/pages/benefits/[category].astro` — 동적 카테고리 페이지
- `src/layouts/BlogPost.astro` — `/benefits` 링크 + hero 이미지 센터링 CSS
- `src/components/Header.astro` — 모바일 햄버거 메뉴 네비게이션
- `~/.env.common` — `CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL` 글로벌 API 키 추가

## How
- IIFE 스코프 문제 진단 → `window.functionName = functionName` 패턴으로 모든 콜백 노출
- `dist/persona-stats.json` (25MiB, Cloudflare 25MiB 업로드 제한 초과) 제거 후 배포
- Global API Key (`cfk_...`)로 인증 방식 변경

## Verification
- `npm run build` — 2,465 pages, 0 errors
- `wrangler pages deploy` — Production 배포 성공 (commit `3c2a4d5`)
- Production URL: `https://94b78cdd.money-aikorea24.pages.dev`
