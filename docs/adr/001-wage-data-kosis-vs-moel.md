# ADR-001: 직업별 임금 추정 데이터 소스 (KOSIS OpenAPI → 고용노동부 CSV)

**상태:** Accepted (2026-05)  
**관련 코드:** `src/data/wage-table.json`, `src/data/job-category-map.json`, `src/pages/persona/[...slug].astro`

## 컨텍스트

페르소나 결과 페이지 **「직업군 TOP5」** 옆에 직업별 **추정 월급(만원)** 뱃지를 표시해야 했다. 초기에는 통계청 KOSIS OpenAPI(`statisticsData.do`)로 **직종 × 성별 × 연령** 교차표를 한 번에 가져오려 했다.

## 시도: KOSIS OpenAPI

| 항목 | 내용 |
|------|------|
| API | KOSIS `statisticsData.do` (표 ID·분류·기간 파라미터 조합) |
| 목표 | KSCO(또는 대분류) × 성별 × 연령대 **3축** 월임금/월급여 교차 |
| 결과 | 해당 조합의 **단일 교차표가 API로 제공되지 않음** (축을 나눠 조회·병합해도 직종 세분 × 성·연령 동시 보정에 필요한 구조 부재) |
| 부가 이슈 | 표마다 분류체계·주기 상이, 직종명이 Nemotron `jobs` 키(2,120종)와 1:1 대응되지 않음 |

**판단:** KOSIS는 코호트 **소득·백분위** 보정(`persona-stats.json`의 `income` 필드, `scripts/patch-income.mjs`)에는 유지하되, **직업 TOP5 옆 임금 뱃지**용으로는 적합하지 않음.

## 결정: 고용노동부 고용형태별근로실태조사 CSV

| 항목 | 내용 |
|------|------|
| 원천 | 고용노동부 **고용형태별근로실태조사** 공표 자료 (월급여액, 만원) |
| 저장 | `src/data/wage-table.json` — 직종 대분류 **10개** 평균 + 성·연령 **보정계수** |
| 매핑 | `src/data/job-category-map.json` — Nemotron 직업명 **2,120종** → 키워드 규칙 → 10개 카테고리 (`fallback`: `사무종사자`) |
| 계산식 | `추정 월급 = jobCategory[카테고리] × ageSexFactor[성별][연령구간]` (무직·0원 직종은 `null`) |
| 구현 | `mapJobToCategory()`, `ageToFactorKey()`, `getJobWage()` in `persona/[...slug].astro` |

이전 구현(인라인 `JOB_WAGE` 키워드 맵, `*.bak.wage`)은 KOSIS/KSCO **일부 키워드**만 반영해 커버리지가 낮았음. 현재 방식은 **대분류 10개 + 보정계수**로 일관성 확보.

## 결과 (코드베이스 검증, 2026-05-25)

- `persona-stats.json` 내 **고유 직업명 2,120개**
- 규칙 매칭 후 **fallback(`사무종사자`)만 적용되는 직업명: 175개 (8.3%)**
- UI 노트는 아직 "KOSIS 고용형태별근로실태조사" 문구가 남아 있음 → **표기는 MOEL 기준으로 정리 권장** (직종 평균 출처와 코호트 `income` KOSIS 출처 혼동 방지)

## 향후 다시 KOSIS를 쓸 때

1. **목적을 분리:** 코호트 소득(`income_*`) vs 직업 리스트 임금 뱃지
2. OpenAPI 전에 KOSIS 웹 UI에서 **동일 3축 표 존재 여부** 먼저 확인
3. Nemotron 직업명 → KSCO 대분류 매핑 테이블을 **별도 유지** (`job-category-map.json` 패턴 재사용)

## 관련 문서

- [TECHNICAL.md §6.5 직업별 임금 추정](../TECHNICAL.md#65-직업별-임금-추정-최근)
- [TECHNICAL.md §4.1 페르소나 데이터 출처](../TECHNICAL.md#41-persona-statsjson)
