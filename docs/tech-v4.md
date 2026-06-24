# persona.aikorea24.kr 기술/전략 문서 v4

**작성일:** 2026년 5월 24일
**대상:** persona.aikorea24.kr (Cloudflare Pages: money-aikorea24)
**상태:** 기능 90% 완성 / 배포·노출·품질 인프라 미완

---

## 1. 한 줄 요약

**"좋은 사이트를 만들었지만 사용자에게 도달하지 않은 상태."** 코드는 충분히 만들었으나 (1) 5/19 이후 미배포, (2) 카드 1,549개 누락, (3) 인접 페이지 near-duplicate, (4) Google 색인 0개의 4중 병목으로 트래픽 월 55 PV.

---

## 2. 기술 스택 (실측)

| 항목 | 내용 |
|---|---|
| 프레임워크 | Astro v6.1.8 (SSG, output: static) |
| 통합 | @astrojs/mdx, @astrojs/sitemap, @astrojs/cloudflare 13.5.2 |
| 배포 | Cloudflare Pages (project: money-aikorea24) |
| Edge Functions | Cloudflare Pages Functions (functions/) |
| DB | Cloudflare D1 (binding: DB, db: persona-db) |
| 인증 | 카카오 OAuth (functions/api/auth/callback/kakao.js) |
| OG 이미지 | 정적 JPG 600x600 (public/cards/{region}_{sex}_{age}.jpg) + 302 redirect |
| 광고 | AdSense 자동광고 (ca-pub-5938862195544185) |
| 분석 | GA4 (G-NG7D2EHJBV) |
| 검색엔진 | 네이버 검증 ✅ / GSC 등록 ✅ / 색인 0개 ❌ |

---

## 3. 페이지 구조

| 경로 | 페이지 수 | 비고 |
|---|---|---|
| / | 1 | 랜딩 |
| /my-persona | 1 | 2단계 입력 (1,003줄 SPA) |
| /persona/[...slug] | 2,891 | 결과 페이지 (1년·10년 키 혼재) |
| /decade/[...slug] | 204 | 10년 단위 (SEO용) |
| /blog | 114 HTML (124 md) | 금융·지원금 콘텐츠 |
| /community | 동적 | D1 백엔드 |
| 정적 | 6 | about, privacy, terms 등 |
| **총** | **3,220** | dist 470MB |

---

## 4. 핵심 데이터 자산

| 파일 | 크기 | 레코드 | 출처 |
|---|---|---|---|
| public/persona-stats.json | 19MB | **2,891 키** | Nemotron + KOSIS |
| public/benefits-clean.json | 3.4MB | — | 정제 |
| public/benefits-curated.json | 16KB | **24건** | 큐레이션 |
| public/blog-match.json | 10KB | 107건 매핑 | TF-IDF |
| public/cards/*.jpg | 평균 100KB | **1,342개 (1,549개 누락)** | 5/9 일괄 생성 |

---

## 5. 소득 추정 로직 (v3 유지)

4축 보정 (직종 가중평균 × 성별·연령 × 지역 × 백분위), KOSIS 2025 실측 기준.

---

## 6. 페르소나 타입 (11종)

연령 × 혼인 × 직업 × 성별 조합. "배우자와 노후를 보내는 사람" / "월급날만 기다리며 버티는 가장" 등 상황묘사형 카피.

---

## 7. 지원금 매칭 엔진

**파일:** src/lib/benefitMatcher.ts (5,493 bytes)

**점수 체계 (실측):**
- 기본 50점
- 연령 매칭: +20 / 불일치: 즉시 제외
- 성별 매칭: +10 / 불일치: 즉시 제외
- 지역 매칭: +15 / 불일치: 즉시 제외
- **큐레이션 boost: +25** (최대 가점)
- 카테고리 보너스: +10
- 소득/재산 조건: -3
- url 없음: -5
- 컷오프: 35점 초과만 노출, 상위 8개

**결과:** 큐레이션 24건이 +25 boost로 거의 모든 페이지 상위 점령 → 페이지 간 차별성 감소.

---

## 8. OG 이미지 전략

동적 SVG 포기, 정적 JPG 사전 생성 선택 (카카오톡 호환성).
**문제:** 1,549개 누락, 5/9 이후 갱신 0, 600x600 (페이스북엔 작음).

---

## 9. 인증·커뮤니티

| 모듈 | 파일 |
|---|---|
| 카카오 OAuth | functions/api/auth/callback/kakao.js |
| 세션 | functions/api/_shared/session.js (HMAC-SHA256) |
| 로그아웃 | functions/api/auth/logout.js |
| 게시글 | functions/api/community/posts.js |
| 댓글 | functions/api/community/comments.js |
| 좋아요 | functions/api/community/like.js |

---

## 10. 결과 페이지 구성 (11블록)

1. 히어로 (페르소나 카드 JPG)
2. 카카오 공유 버튼
3. "당신은..." 카피 4문장
4. KPI 그리드 (아파트%·대졸%·기혼%·무직%)
5. 추정 월소득 + 백분위 게이지
6. 주거·학력·직업·혼인 바 차트
7. 같은 조건 한국인의 하루
8. **BenefitCards (지원금 8개)** ← v3 누락 항목
9. 다른 지역/연령/성별 비교 링크
10. 관련 금융 가이드 (blog-match)
11. 운세 + 카운터 + CTA

---

## 11. 트래픽·색인 진단

### 11.1 GA4 (4/26~5/23)
- 활성 사용자: **12명**
- 총 조회수: **55**
- 평균 참여 시간: **18초**
- 한국인 페르소나 페이지가 94.5% 점유

### 11.2 GSC
- 발견된 페이지: **3,000개**
- 색인된 페이지: **0개**
- 총 클릭: **0회**
- 색인 거부 추정 사유 (확신도 순):
  1. **near-duplicate** (90%) — 인접 1살 단위 페이지 간 통계 거의 동일
  2. 신규 사이트 페널티 (70%) — 6개월 미만
  3. 권위 부족 (60%) — 백링크 0
  4. 클라이언트 사이드 로딩 의심 (30%) — /my-persona 무한 로딩
  5. internal link graph 약함 (50%)

---

## 12. ★ Critical 이슈 (4중 병목)

### 12.1 5/19 이후 미배포 (Critical)
- 마지막 commit: 2026-05-19 09:00:54
- 미커밋 파일: **49개**
- 미배포 자산: benefits 3종 (14.4MB), benefitMatcher.ts, BenefitCards.astro, functions/ 전체
- 라이브 사이트는 5/19 이전 버전

### 12.2 카드 1,549개 누락 (Critical)
- 80~99세: 711개 누락 (가장 큼)
- 1년 단위 일부: 약 600개 누락
- 10년 단위 키: 204개 누락 (의도된 누락)
- 카드 mtime: 5/9 일괄 생성 후 갱신 0
- 페르소나 네이밍 11개·KOSIS 소득 데이터가 카드에 반영 안 됨

### 12.3 페이지 차별성 부족 (Critical)
- 인접 1살 단위 페이지가 통계상 거의 동일
- 큐레이션 24건이 모든 페이지 상위 점령
- Google 색인 거부의 핵심 원인

### 12.4 /my-persona 무한 로딩 (High)
- generateCanvas의 img.onerror 부재
- 80세 이상 + 누락 카드 입력 시 멈춤 가능성
- runAnalyze try/catch 흐름 정밀 점검 필요

---

## 13. 자매 사이트 시너지

| 사이트 | 역할 | 활용 방안 |
|---|---|---|
| senior.informationhot.kr | 노인 복지 자동 블로그 | 50~70대 페르소나 결과 페이지에 백링크 |
| 2.techpawz.com | 자동 블로그 | 백링크, 콘텐츠 재활용 |

blog-match.json 인프라가 이미 있으므로 외부 도메인 글 매칭으로 확장 가능.

---

## 14. 바이럴 가능성 (6/10)

| 요소 | 점수 | 비고 |
|---|---|---|
| 호기심 hook | 8/10 | "나와 같은 한국인" 강력 |
| 결과 차별성 | 5/10 | 숫자 차이가 사용자에겐 미묘 |
| 공유 동기 | 4/10 | MBTI 아닌 통계, 자랑거리 약함 |
| 시각적 임팩트 | 6/10 | 600x600, 같은 배경 재사용 |
| 마무리 카피 | 3/10 | "%가 아파트…" 평범 |

**개선 방향:** 단일 강렬 문장 + 페르소나별 배경 다양화 + "상위 13% 안에 들어요" 같은 자존감 자극.

---

## 15. 실행 우선순위

### Phase 0 (오늘): 4중 병목 중 가장 큰 것 해소
1. **로컬 49개 변경 커밋 + 배포** (10분)
2. **카드 누락 1,549개에 onerror fallback 추가** (15분, og-default.png로 폴백)
3. /my-persona runAnalyze의 generateCanvas 비동기 흐름 점검·수정

### Phase 1 (이번 주)
4. **누락 카드 1,549개 일괄 재생성** (scripts/generate-mobile-cards.js)
5. **카드 생성 로직 갱신**: 페르소나 네이밍 11개, KOSIS 소득 반영
6. **페이지 차별성 강화**:
   - 페르소나 타입별로 노출되는 큐레이션 다르게
   - "이 페르소나만의 인사이트" 1줄 자동 생성
   - 1년 단위 페이지의 canonical을 10년 단위로 통합 검토 (또는 1년 단위 noindex)

### Phase 2 (1~3개월)
7. /compare/ 페이지 (페르소나 2개 비교, 공유 유발)
8. 지원금 상세 페이지 자체 보유
9. senior.informationhot.kr ↔ persona 양방향 백링크 5~10건
10. 커뮤니티 시드 게시글 30~50개

### Phase 3 (검토만)
11. 1만 페이지 양산은 GSC 색인률 30% 이상 검증된 뒤 결정

---

## 16. 1만 페이지 양산 평가 (결론)

**비추천 (현 시점).**

이유:
- 현재 3,220개도 색인 0개
- 1만 개 양산해도 같은 near-duplicate 패턴이면 색인 0개 유지
- 양산보다 **현재 페이지의 색인률·차별성·체류시간** 끌어올리기가 ROI 10배 이상

**조건부 추천:**
Phase 0~2 완료 후 GSC 색인률 30% 이상 + 평균 체류 60초 이상 도달 시 시군구 단위 확장 검토.

---

## 17. 변경 이력

| 버전 | 일자 | 변경 |
|---|---|---|
| v3 | 2026-05-19 | 초기 작성 |
| v4 | 2026-05-24 | 실측 기반 숫자 정정, 4중 병목 진단, GSC/카드 누락/차별성/무한로딩, Phase 로드맵 |

