# PLAN.md — Phase 6: Income Gauge Deep Link & Card Income Integration

**Status**: Planning Complete (not yet executed)  
**Version**: 1.0 (2026-07-29)  
**Total Effort Estimate**: ~3-4 hours (4 independent work items, can parallelize)

---

## Goal

4개 누락된 income 데이터 연동을 완료하여 persona SSG 페이지 + my-persona SPA + 카드 이미지 전반에서 소득 정보가 일관되게 표시되도록 한다. 구체적으로:

1. **B**: 카드 이미지(서버 JPG + 모바일 + 클라이언트 캔버스)에 income bar/overlay 추가
2. **D**: og:image URL v2 마이그레이션 (캐시 무력화)
3. **A**: SSG persona 페이지에 benefit deep link 버튼 추가
4. **C**: my-persona `compareWithData()`에서 income 데이터 추출

---

## Work Items

### [A] SSG Benefit Deep Link (`[...slug].astro`)
**Status**: Pending · **Effort**: ~20min

**What**: 페르소나 SSG 페이지 하단에 "내 소득에 맞는 지원금 찾기" 버튼 추가

**Technical details**:
- 위치: `[...slug].astro`의 income gauge 섹션 하단 (기존 게이지 영역 after, ~line 633)
- HTML: `<a href="/benefits?income={incomeVal}&age={age}&region={region}&sex={sex}" class="income-benefit-link">내 소득에 맞는 지원금 찾기 →</a>`
- 데이터: frontmatter에서 `s.income.income_employed` (incomeVal), `key` 파싱 (age/region/sex)
- 스타일: Tailwind 클래스 + 기존 디자인 시스템 버튼 스타일 준수
- **주의**: 비어있는 income 필드(null)인 경우 버튼 미표시

**Prerequisite check — benefits URL 파라미터**:
- `/benefits` 페이지는 현재 URL 쿼리 파라미터를 읽지 않음
- `benefits/index.astro`의 client-side JS에 URLSearchParams 처리 추가 필요 (Task A-1)
- benefits-clean.json은 `age_range`(배열) + `regions`(배열) 필드를 가지고 있음
- 510건의 benefit이 `target` 필드에서 "소득" 언급 (텍스트 매칭 가능)
- 필터 로직: `age_range`가 age 포함 + `regions`에 region 포함 → 매칭. fallback으로 target 텍스트 매칭.

**Sub-tasks**:
| # | Task | File | Detail |
|---|------|------|--------|
| A-1 | benefits URL param 필터 추가 | `benefits/index.astro` | `<script>` 내 `initFromUrl()` 함수 추가: `?income=&age=&region=&sex=` 읽어 필터링 |
| A-2 | SSG button 추가 | `[...slug].astro` | income gauge 하단 deep link 버튼 |

**Verification**:
- [ ] `npm run build` 성공 (빌드 전: 2459p 기준 기록, 빌드 후 0에러)
- [ ] `/persona/서울-남자-32/` 하단에 "내 소득에 맞는 지원금 찾기" 버튼 존재
- [ ] 버튼 클릭 시 `/benefits?income=...&age=...&region=...&sex=...` 이동
- [ ] `/benefits?age=32&region=서울&sex=남자` 접속 시 age_range=32 포함 benefit만 필터링됨
- [ ] income=null인 페르소나(데이터 부족)에서 버튼 미표시
- [ ] 기존 benefits 필터(tab/search/pagination)와 충돌 없음

---

### [B] Card Income Bar (B-1: Server JPG, B-2: Mobile, B-3: Client Canvas)
**Status**: Pending · **Effort**: ~40min (B-1) + ~20min (B-2) + ~30min (B-3)

#### B-1: Server JPG Card (`generate-missing-cards.mjs`)
**What**: `makeSvgOverlay()`에 income bar 추가

**Technical details**:
- 기존 4개 bar [aptP, eduP, marP, uneP]는 건드리지 않음 (additive)
- 5번째 bar 추가: incomeP (소득 백분위)
  - 레이아웃: 기존 bar와 동일한 스타일(X좌표, 너비, 폰트, 색상)
  - 데이터: `STATS[key].income.top_percentile` → bar width
  - 라벨: `income_employed` (포맷: "456만원" 또는 "4,567만원")
- `STATS[key].income`이 null/undefined면 bar 미표시 (skip)
- 기존 4개 bar와의 시각적 충돌 방지: 기존 bar 하단 또는 적절한 위치에 배치

**Data flow**:
```
persona-stats.json → STATS[key].income.income_employed (소득액)
                   → STATS[key].income.top_percentile (상위 %)
```

**Verification**:
- [ ] `--dry-run` 모드: 1장 카드만 생성하여 income bar 존재 확인
- [ ] 전체 재생성 완료 (2,244장)
- [ ] income bar가 기존 4개 bar와 동일한 스타일로 렌더링됨
- [ ] income=null 페르소나는 bar 미표시

#### B-2: Mobile Card (`generate-mobile-cards.js`)
**What**: `makeSvg()`에 income bar 추가 (mobile 해상도)

**Technical details**:
- B-1과 동일한 로직, 모바일 SVG 템플릿에 맞게 좌표/크기 조정
- Mobile 카드 해상도: 465x797
- 기존 bar 레이아웃 그대로, incomeP만 추가

**Verification**:
- [ ] Mobile 카드에도 income bar 정상 렌더링
- [ ] 모바일 해상도에서 글자 잘림 없음

#### B-3: Client Canvas (`my-persona.astro`)
**What**: `generateCanvas()`에 income overlay 텍스트 추가

**Technical details**:
- 위치: 기존 4개 text overlay 하단 (canvas drawText)
- 내용: "소득 상위 {topPercentile}% ({incomeEmployed}만원)"
- `compareWithData()` (line 536-561)에서 income 비교 로직 추가 (3줄):
  ```js
  const myIncome = stats.income?.income_employed || 0;
  const theirIncome = d.income?.income_employed || 0;
  // → 비교 결과를 결과 섹션에 표시
  ```
- 데이터 소스: `s.income` (my-persona는 decade-stats.json 사용)

**Source reference** (`[...slug].astro:602-633`): income gauge CSS 템플릿
```astro
<div class="youare-income">
  <p class="stat-label">소득</p>
  <p class="stat-value">{s.income_employed?.toLocaleString() ?? '...'}만원</p>
  <div class="gauge-track">
    <div class="gauge-fill" style="width: {s.top_percentile}%"></div>
  </div>
  <p class="stat-compare">상위 {s.top_percentile}%</p>
</div>
```

**Verification**:
- [ ] my-persona 결과 화면에 income 비교 노출
- [ ] 캔버스 다운로드 이미지에 income overlay 포함
- [ ] income=null인 경우 "데이터 없음" 처리

---

### [C] my-persona Income Data Extraction (`compareWithData`)
**Status**: Pending · **Effort**: ~5min

**Technical details**:
- B-3에 포함됨 (B-3 작업 시 `compareWithData()` 수정)
- `compareWithData()`의 stats-map 객체에 `d.income.income_employed`와 `d.top_percentile` 추가
- 3줄 추가: income_employed 비교 → UI 표시
- 기존 structure(apt/edu/mar/une)와 동일한 비교 패턴 적용

---

### [D] og:image URL v2 Migration
**Status**: Pending · **Effort**: ~5min

**What**: B-1 카드 재생성 직후 og:image CDN URL 버전을 `v=2`로 업데이트

**Technical details**:
- `[...slug].astro` line 322-329: og:image URL 변경
  ```astro
  og:image: `https://cards.persona.aikorea24.kr/${key}.jpg?v=2`
  ```
- `functions/og/index.js`: v1→v2 리다이렉트 처리 확인 (필요시)
- 변경 시점: B-1 서버 카드 재생성 **직후** (이미지가 CDN에 배포된 후)
- `v=2` 목적: 기존 og:image CDN/Twitter/카카오 캐시 강제 무효화 (기존 이미지에는 income bar가 없으므로)

**Verification**:
- [ ] 빌드 후 dist/ HTML에서 og:image URL에 `v=2` 확인
- [ ] og debugger에서 새 이미지 로드 확인

---

## Execution Order

```
Phase 6 Execution Plan:

Step 1: Verify baseline (npm run build passes before any change)
  ↓
Step 2 [B-1]: Update generate-missing-cards.mjs → --dry-run test → full regen
  ↓
Step 3 [B-2]: Update generate-mobile-cards.js
  ↓                          ↓
Step 4 [D]: og:image v=2     └─ Step 5 [B-3 + C]: my-persona.astro
  ↓
Step 6 [A-1]: benefits URL param filter
  ↓
Step 7 [A-2]: SSG deep link button
  ↓
Step 8: Final build verification (npm run build)
Step 9: Deploy (npm run deploy)
```

**Parallelization note**: Steps 2-3 (B-1, B-2) can run in parallel. Steps 5-7 (B-3, A-1, A-2) can run in parallel. Step 4 must follow Step 2.

---

## Dependencies

| Work Item | Depends On | Wait For |
|-----------|-----------|----------|
| D (og:image v2) | B-1 (card regen) | 카드 재생성 완료 + CDN 배포 |
| A-2 (SSG button) | A-1 (benefits filter) | benefits 필터 로직 완료 |
| A-2 (SSG button) | — | benefits URL scheme 확정 |
| B-2 (mobile card) | B-1 pattern | B-1의 income bar SVG 패턴 |
| C (my-persona income) | — | 독립 실행 가능 (패턴만 B-1 참조) |
| A-1 (benefits filter) | — | benefits-clean.json 필드 구조 확인 |

---

## Verification Checklist (Final)

**Build**:
- [ ] `npm run build` 성공 (pre-build count, post-build 0-error)

**SSG Persona Page**:
- [ ] 기존 income gauge 정상 동작 (회귀 없음)
- [ ] Benefit deep link 버튼 존재 (income 있을 때만)
- [ ] og:image URL v=2

**my-persona**:
- [ ] compareWithData() income 추출 → 화면 표시
- [ ] generateCanvas() income overlay 포함

**Card Images**:
- [ ] serve card 1장 임의 추출: income bar 존재
- [ ] mobile card 1장 임의 추출: income bar 존재
- [ ] 기존 4개 bar 레이아웃/스타일 변경 없음

**Benefits**:
- [ ] URL `?age=32&region=서울&sex=남자` 필터 정상 동작
- [ ] tab/search/pagination과 충돌 없음

**Deploy**:
- [ ] `npm run deploy` 성공
- [ ] Production 카드 CDN에서 income bar 포함 이미지 로드

---

## Rollback Plan

각 작업은 독립적이므로 부분 롤백 가능:

| Work Item | Rollback Action |
|-----------|----------------|
| A (SSG + benefits) | `git revert` A-1/A-2 커밋 |
| B-1 (server card) | `git revert` B-1 커밋 + v1 카드 재배포(원복 필요시) |
| B-2 (mobile card) | `git revert` B-2 커밋 |
| B-3 + C (my-persona) | `git revert` 해당 커밋 |
| D (og:image v2) | `git revert` → v1로 원복 |
