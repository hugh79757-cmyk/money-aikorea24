---
date: 2026-07-09
type: fix
status: resolved
---

# AdSense auto-ads가 related-grid 내부에 삽입되어 카드 1,2번 클릭 불가

## What
블로그 페이지 하단 "📌 관련 글 더 보기" 섹션의 3개 카드 중 1,2번째만 클릭되지 않는 버그 수정.

## Why
Google AdSense auto-ads가 `.related-grid`(CSS grid, `<div>`) 내부에 `<ins>` 요소를 동적으로 삽입하여 grid 구조가 깨지고, 삽입된 광고가 앞쪽 카드들을 오버레이하여 클릭을 가로막음. 3번째 카드는 광고 아래쪽에 있어 정상 동작.

## Files changed
- `src/layouts/BlogPost.astro` (lines 289-300, 440-452)

## How
`.related-grid`를 `<div>`에서 `<ol>`(ordered list)로 변경하고 각 카드를 `<li>`로 래핑. AdSense auto-ads는 `<ol>` 내부에 삽입되면 invalid HTML이 되므로 회피함. CSS에 `list-style: none; padding: 0; margin: 0` 추가로 시각적 동일함 유지.

## Verification
- 빌드 성공 (2,455 pages, 0 errors)
- Production 배포 후 `persona.aikorea24.kr`에서 3개 카드 모두 클릭 정상 동작 확인
