# PLAN.md — Phase 03: AdSense Revenue Optimization

## Goal
RPM 최적화를 위해 본문 중간 in-article 광고, PC 리더보드, 모바일 스티키를 추가하고 IntersectionObserver 기반 레이지로드 적용.

## Tasks

### Task 1: consts.ts에 ADSENSE_CLIENT 상수 추가
**파일**: `src/consts.ts`
**작업**:
- `ADSENSE_CLIENT: "ca-pub-5938862195544185"` 추가
- 하드코딩된 12곳을 이 상수로 교체 (점진적)

### Task 2: in-article.html 파셜 생성
**파일**: `src/components/adsense/in-article.html`
**작업**:
- `class="adsbygoogle lazyad"` (자동광고가 스캔하지 않도록)
- `data-ad-layout="in-article"`, `data-ad-format="fluid"`
- `data-ad-client="ca-pub-5938862195544185"`, `data-ad-slot="8107272066"`
- `style="display:block; text-align:center;"`만 인라인
- 래퍼 `div.ad-inarticle`
- push 스크립트 포함하지 않음

### Task 3: leaderboard.html 파셜 생성
**파일**: `src/components/adsense/leaderboard.html`
**작업**:
- `class="adsbygoogle lazyad desktop-only"`
- `data-ad-client="ca-pub-5938862195544185"`, `data-ad-slot="8107272066"`
- `data-ad-format="horizontal"`
- 래퍼 `div.ad-leaderboard desktop-only`

### Task 4: mobile-sticky.html 파셜 생성
**파일**: `src/components/adsense/mobile-sticky.html`
**작업**:
- `class="adsbygoogle lazyad"`, `id="mobile-sticky-ad"`
- `data-ad-client="ca-pub-5938862195544185"`, `data-ad-slot="8107272066"`
- `style="display:none"` (JS가 block 처리)
- 닫기 버튼 (`aria-label` 포함) + `div.ad-mobile-sticky`
- `data-ad-format="horizontal"`

### Task 5: BlogPost.astro 마커 기반 광고 삽입
**파일**: `src/layouts/BlogPost.astro`
**작업**:
- 기존 수동 광고 3개 제거
- `$content`에 마커 주입:
  - 첫 `</p>` 직후 → `<!--AD1-->` (WordCount >= 800)
  - 첫 `<h2>` 앞 → `<!--AD2-->` (WordCount >= 800)
  - 세 번째 `<h2>` 앞 → `<!--AD3-->` (고단가 카테고리 + WordCount >= 800)
- 마커를 각 파셜로 치환 (`| safeHTML`)
- WordCount < 800: 마커 없이 리더보드만 추가

### Task 6: BaseHead.astro IntersectionObserver 스크립트
**파일**: `src/components/BaseHead.astro`
**작업**:
- `</body>` 직전에 글로벌 lazy load 스크립트 추가
- IntersectionObserver로 `ins.lazyad` 관찰
- `rootMargin: "400px 0px"`, `threshold: 0`
- 콜백: `(adsbygoogle = window.adsbygoogle || []).push({})` 한 번만
- `data-adsbygoogle-status` 속성으로 중복 방지
- 모바일 스티키: `window.scrollY > 600` 시 display:block

### Task 7: global.css 광고 스타일
**파일**: `src/styles/global.css`
**작업**:
- `.ad-inarticle`: `margin: 32px 0; min-height: 250px; min-width: 300px`
- `.ad-leaderboard`: `margin: 24px auto; min-height: 90px; min-width: 728px`
- `.ad-mobile-sticky`: `position: fixed; bottom: 0; z-index: 9998; display: none`
- `.desktop-only` / `.mobile-only` 미디어쿼리 (768px 기준)
- 다크모드: `ins.adsbygoogle` 배경 `#fff` 유지
- **금지**: `.adsbygoogle + .adsbygoogle { display:none }` 절대 없음
- `ins.adsbygoogle[data-ad-status="unfilled"] { display: none !important }` 추가

## Dependencies
- Task 1 → Task 2, 3, 4 (상수 필요)
- Task 2~4 → Task 5 (파셜 필요)
- Task 5, 6은 독립적

## Estimated Effort
- Task 1: 5분
- Task 2~4: 각 10분 (파셜 생성)
- Task 5: 20분 (마커 로직)
- Task 6: 15분 (IntersectionObserver)
- Task 7: 10분 (CSS)
- **총: ~60분**

## Verification
1. `npm run build` 빌드 성공
2. DevTools Console에 TagError 없음
3. `ins.adsbygoogle.lazyad`가 AD1/AD2/AD3 자리에 존재
4. 스크롤 시 `data-adsbygoogle-status="done"` 속성 부여
5. PC에서 리더보드 본문 끝 노출
6. 모바일(375px)에서 스크롤 600px 이후 스티키 노출
7. 다크모드 토글 시 광고 영역 흰 배경
8. WordCount < 800 글에서 본문 중간 광고 0개
