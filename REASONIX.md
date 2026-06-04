# Reasonix project memory

Notes the user pinned via the `#` prompt prefix. The whole file is
loaded into the immutable system prefix every session — keep it terse.

- 작업 목표
persona.aikorea24.kr 의 페르소나 결과 페이지(예: /persona/서울-남자-35/)에
블로그 글 추천 섹션을 추가한다.

---

# 사이트 기술 스택
- Framework: Astro 6 (SSR, Cloudflare Pages adapter)
- Styling: Tailwind CSS (기존 클래스 스타일과 통일)
- Database: Cloudflare D1
- 기존 블로그 검색 인덱스: /search.json (GET, public)
  - 필드: title, description, slug, category, pubDate
  - category 값: "insurance" | "invest" | "loan" | "tax" | "general"

---

# 현재 페르소나 페이지 구조 파악

1. 페르소나 결과 페이지 라우트 파일을 찾아라.
   - 경로 예시: src/pages/persona/[slug].astro 또는 유사 경로
2. 해당 파일에서 아래 변수가 어떻게 선언되어 있는지 확인해라.
   - age (숫자)
   - sex ("남자" | "여자")
   - married (boolean 또는 혼인상태 문자열)
   - province (지역명 문자열, 예: "서울", "부산")
3. 페이지 내 "💡 금융 인사이트" 섹션의 HTML/Astro 마크업을 찾아라.
   → 이 섹션 바로 아래에 추천 섹션을 삽입할 것이다.

---

# 구현할 기능

## A. 추천 로직 (서버사이드, Astro frontmatter에서 처리)

search.json을 fetch해서 전체 글 목록을 가져온 뒤,
아래 규칙으로 각 글에 relevanceScore를 계산하고
상위 4개를 추출한다.

### 점수 계산 규칙

**연령대 키워드 (age 기준)**
- age 19~29 → 키워드: ["청년", "청년도약", "청년적금", "주휴수당", "중소기업취업", "전세대출", "비상금"] 각 +3점
- age 30~39 → 키워드: ["주담대", "청약", "IRP", "ISA", "연말정산", "실손보험", "육아", "부모급여"] 각 +3점
- age 40~49 → 키워드: ["종합소득세", "절세", "ETF", "상속", "증여", "암보험", "간병"] 각 +3점
- age 50~64 → 키워드: ["상속세", "증여세", "노후", "연금", "간병인보험", "건강보험"] 각 +3점
- age 65+  → 키워드: ["상속", "증여", "간병", "실버", "노후", "의료비"] 각 +3점

**성별 키워드 (sex 기준)**
- 여자 → ["태아보험", "육아휴직", "근로장려금", "실손보험"] 각 +2점
- 남자 → ["주담대", "청약", "실업급여", "IRP"] 각 +2점

**혼인 상태 키워드 (married 기준)**
- 기혼(true 또는 "기혼") → ["혼인세액공제", "육아", "부모급여", "아동수당", "태아보험"] 각 +2점
- 미혼              → ["청년", "전세", "비상금대출"] 각 +2점

**카테고리 보너스**
- insurance(보험) 카테고리 글: +1점 (보험은 전 연령 범용)
- tax(세금) 카테고리 글: +1점

### 점수 계산 방식
- title + description 텍스트를 소문자로 합친 뒤
  위 키워드가 포함되면 해당 점수를 누적한다.
- 동점이면 pubDate 최신순으로 정렬한다.
- 최종 상위 4개를 selectedPosts로 추출한다.

---

## B. UI 컴포넌트

새 파일 src/components/PersonaBlogRecommend.astro 를 생성한다.

### Props
- age: number
- sex: string
- married: boolean
- province: string

### 렌더링 조건
- selectedPosts가 1개 이상일 때만 섹션을 렌더링한다.
- selectedPosts가 0개면 아무것도 렌더링하지 않는다.

### HTML 구조 (기존 페이지 디자인 시스템에 맞게)

섹션 제목:
  "📚 {province} {age}대 {sex}에게 추천하는 금융 가이드"
  예) "📚 서울 30대 남자에게 추천하는 금융 가이드"
  → age는 10의 자리만 사용 (Math.floor(age/10)*10)

카드 레이아웃:
  - 최대 4개 카드, 가로 2열 그리드 (모바일은 1열)
  - 각 카드:
    - 카테고리 뱃지 (기존 .badge 클래스 사용)
      - insurance → "🛡️ 보험"
      - invest    → "📈 투자·절세"
      - loan      → "🏠 대출·부동산"
      - tax       → "💰 세금·절약"
      - general   → "📋 금융"
    - 글 제목 (h3)
    - 설명 2줄 말줄임 (description)
    - "읽기 →" 링크
    - href: /blog/{slug}/

하단:
  - "📝 금융 가이드 전체 보기 →" 버튼 → /blog/ 로 링크

---

## C. 페르소나 결과 페이지에 컴포넌트 삽입

1. 라우트 파일 상단 frontmatter에 import 추가:
   import PersonaBlogRecommend from '@/components/PersonaBlogRecommend.astro';
   (또는 실제 경로에 맞게)

2. "💡 금융 인사이트" 섹션을 담은 태그를 찾아서
   그 닫는 태그 바로 뒤에 아래를 삽입:

   <PersonaBlogRecommend
     age={age}
     sex={sex}
     married={married}
     province={province}
   />

   → age, sex, married, province 변수명은
     실제 파일에서 사용 중인 변수명으로 맞게 수정할 것.

---

# 주의사항

1. search.json fetch는 서버사이드(Astro frontmatter)에서 처리한다.
   클라이언트 JS로 처리하지 않는다.
   (SSR이므로 빌드 타임이 아닌 요청 타임에 fetch)

2. fetch 실패 시 빈 배열로 fallback 처리하여
   페이지 렌더링이 깨지지 않도록 한다.

3. 기존 페이지의 CSS 클래스(.badge, .card-top, .read-more 등)를
   최대한 재사용한다. 새 클래스를 추가할 경우
   컴포넌트 내 <style> 태그에 scoped로 작성한다.

4. 작업 전 반드시 실제 라우트 파일을 열어서
   변수명(age/sex/married/province)이 어떻게 선언되어 있는지
   확인하고 그에 맞게 코드를 작성한다.

5. TypeScript 에러가 나지 않도록 search.json 응답에
   적절한 타입을 정의한다.

---

# 완료 조건 체크리스트

- [ ] src/components/PersonaBlogRecommend.astro 파일 생성됨
- [ ] 페르소나 결과 라우트 파일에 컴포넌트 import 및 삽입됨
- [ ] /persona/서울-남자-35/ 에서 추천 카드 4개가 노출됨
- [ ] /persona/부산-여자-25/ 에서 청년/여성 관련 글이 우선 노출됨
- [ ] /persona/경기-남자-55/ 에서 상속/노후 관련 글이 우선 노출됨
- [ ] fetch 실패 시 섹션이 사라지고 페이지는 정상 렌더링됨
- [ ] 모바일(375px)에서 1열로 정상 표시됨
- 수정 작업

src/components/PersonaBlogRecommend.astro 에서
현재 getCollection('blog') 로 블로그 글을 가져오는 부분을
아래와 같이 fetch('/search.json') 방식으로 교체해라.

## 이유
getCollection은 빌드 타임에 글 목록을 고정하므로
새 글을 올려도 재배포 전까지 추천에 반영되지 않는다.
fetch 방식은 SSR 요청 타임에 실행되므로 항상 최신 글이 반영된다.

## 교체 방법

### 기존 코드 (제거)
import { getCollection } from 'astro:content';
const posts = await getCollection('blog');

### 변경 코드 (적용)
const posts: SearchItem[] = await fetch(
  new URL('/search.json', Astro.url).href
)
  .then((r) => r.json())
  .catch(() => []);

## 주의사항
1. fetch URL은 new URL('/search.json', Astro.url).href 로 구성한다.
   (Cloudflare Workers 환경에서 상대경로 fetch가 안 될 수 있음)
2. SearchItem 타입은 기존에 정의된 인터페이스를 그대로 사용한다.
3. 점수 계산 로직, UI 렌더링 로직은 변경하지 않는다.
4. astro build 후 에러 없음을 확인한다.
- 작업 지시: 메인 페이지에 페르소나 인덱스 허브 추가

## 컨텍스트

- 프로젝트: `/Users/twinssn/Projects/money-aikorea24`
- 스택: Astro 6.1.8 (`output: 'static'`) + Tailwind v4 + Cloudflare Pages
- 도메인: https://persona.aikorea24.kr
- 현재 문제: Search Console에 3,000개 페이지가 "발견됨, 색인 미생성" 상태로 대기 중. 메인 페이지(`src/pages/index.astro`)에서 `/persona/*` 페이지로 가는 내부 링크가 **0개**라서 Googlebot이 페르소나 페이지들을 고아 페이지(orphan pages)로 인식하고 있음.
- 이미 빌드된 정적 페이지: `dist/persona/` 안에 2,891개 (1년 단위 + 10년 단위 모두)
- 색인 대상(10년 단위)만 sitemap에 포함됨: 204개 = 17지역 × 2성별 × 6연령

## 목표

`src/pages/index.astro`의 최하단(footer 직전)에 **"지역별 페르소나 둘러보기"** 섹션을 추가하여, 색인 대상 204개 페르소나 페이지 전부로 가는 내부 링크를 만든다. Googlebot이 메인을 1회 크롤할 때 204개 자식 페이지의 발견·우선순위가 동시에 상승하도록 함.

## 데이터 정의 (하드코딩)

다음 배열을 컴포넌트 frontmatter에 선언:

```ts
const REGIONS = [
  '서울', '경기', '인천', '부산', '대구', '대전', '광주', '울산', '세종',
  '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주'
]; // 17개

const GENDERS = ['남자', '여자']; // 2개

const AGE_GROUPS = [
  { label: '20대', slug: '20대' },
  { label: '30대', slug: '30대' },
  { label: '40대', slug: '40대' },
  { label: '50대', slug: '50대' },
  { label: '60대', slug: '60대' },
  { label: '70대 이상', slug: '70대이상' },
]; // 6개

// 총 17 × 2 × 6 = 204개
```

## URL 패턴

각 페르소나 페이지 URL은 다음 형식을 정확히 따른다 (기존 sitemap-0.xml과 100% 일치해야 함):

```
/persona/{지역}-{성별}-{연령slug}/
```

예시:
- `/persona/서울-남자-30대/`
- `/persona/세종-여자-40대/`
- `/persona/제주-남자-70대이상/`

URL의 한글은 Astro의 `<a href>` 안에서 그대로 사용한다 (브라우저가 자동 인코딩). 직접 `encodeURIComponent()` 호출하지 말 것 — 기존 sitemap이 인코딩된 형태로 있고 브라우저가 알아서 처리한다.

## 구현 요구사항

### 1. 파일 수정
- 대상 파일: `src/pages/index.astro`
- 기존 콘텐츠는 **절대 삭제하지 말고**, 메인 콘텐츠와 footer 사이(또는 footer가 별도 컴포넌트라면 마지막 `<section>` 다음)에 새 섹션을 **추가**한다.

### 2. 섹션 구조

```astro
<section class="persona-index-hub" aria-label="지역별 페르소나 인덱스">
  <div class="container">
    <header>
      <h2>지역별 한국인 페르소나 둘러보기</h2>
      <p>17개 광역지자체 × 성별 × 연령대 — 204개 페르소나 분석</p>
    </header>

    {REGIONS.map(region => (
      <article class="region-block">
        <h3>{region}</h3>
        <div class="links-grid">
          {GENDERS.map(gender => (
            AGE_GROUPS.map(age => (
              <a 
                href={`/persona/${region}-${gender}-${age.slug}/`}
                class="persona-link"
              >
                {region} {gender} {age.label}
              </a>
            ))
          ))}
        </div>
      </article>
    ))}
  </div>
</section>
```

### 3. 스타일링 (Tailwind v4 사용)

기존 사이트 디자인 톤(밝은 배경 + 보라/파랑 계열)에 어울리도록:

- 섹션 전체: 상단 여백 큰 패딩(`py-16`), 배경은 살짝 다른 톤(`bg-gray-50` 또는 `bg-slate-50`)
- h2: `text-2xl md:text-3xl font-bold text-center mb-2`
- 설명 문구: `text-sm text-gray-500 text-center mb-10`
- 각 region-block: `mb-8`, h3는 `text-lg font-semibold mb-3 text-gray-800 border-l-4 border-blue-500 pl-3`
- links-grid: `grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2`
- 각 a 태그: `text-sm px-3 py-2 rounded-md bg-white border border-gray-200 text-gray-700 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition-colors text-center`

기존 사이트의 디자인 토큰이 있다면 그것을 우선 사용한다.

### 4. 접근성 및 SEO

- 모든 `<a>`에 `href` 속성 명시 (JavaScript 의존 0)
- `aria-label`로 섹션 목적 설명
- 시맨틱 태그(`section`, `article`, `header`, `h2`, `h3`) 사용
- `rel="nofollow"` 같은 속성은 **추가하지 말 것** (내부 PageRank 흐름이 목적이므로)

## 작업 후 검증 명령

빌드와 검증을 다음 순서로 수행:

```bash
# 1. 빌드
npm run build

# 2. 빌드된 index.html에 페르소나 링크가 정확히 204개 있는지 확인
grep -oE 'href="/persona/[^"]+/"' dist/index.html | sort -u | wc -l
# 기대값: 204

# 3. URL 패턴이 sitemap과 일치하는지 샘플 검증 (10개)
grep -oE 'href="/persona/[^"]+/"' dist/index.html | sort -u | head -10

# 4. sitemap-0.xml의 URL과 교차 검증
# index.html의 모든 페르소나 링크가 sitemap에도 있는지
grep -oE 'href="/persona/[^"]+/"' dist/index.html \
  | sed 's/href="//;s/"$//' \
  | while read url; do
      grep -q "$url" dist/sitemap-0.xml || echo "MISSING IN SITEMAP: $url"
    done
# 기대 출력: (없음 - 전부 매칭되어야 함)

# 5. 결과 요약 출력
echo "✓ 페르소나 링크 개수: $(grep -oE 'href="/persona/[^"]+/"' dist/index.html | sort -u | wc -l)"
echo "✓ sitemap URL 개수: $(grep -c '<loc>.*persona' dist/sitemap-0.xml)"
```

위 5번 출력에서 **링크 개수 = 204, sitemap URL 개수 = 204** 가 일치해야 작업 완료.

## 작업 후 보고할 것

1. 수정한 파일 경로와 변경 라인 수
2. `npm run build` 성공 여부 및 빌드 시간
3. 위 검증 명령 5번의 출력 결과
4. 만약 불일치(MISSING IN SITEMAP)가 나오면 그 URL 목록 전체

## 하지 말 것

- 기존 `index.astro`의 다른 섹션 수정 또는 삭제 금지
- 새 컴포넌트 파일 생성 금지 (이 작업은 `index.astro` 단일 파일 수정으로 끝나야 함)
- `astro.config.mjs` 수정 금지
- 패키지 추가 설치 금지
- 1년 단위 페르소나(`/persona/서울-남자-35/` 같은) 링크 추가 금지 — 오직 10년 단위 204개만
- 작업 지시: 페르소나 페이지에 "결정 카드(Decision Card)" 시스템 구축

## 컨텍스트

- 프로젝트 경로: `/Users/twinssn/Projects/money-aikorea24`
- 스택: Astro 6.1.8 (`output: 'static'`) + Cloudflare Pages + Tailwind v4
- 라이브 도메인: https://persona.aikorea24.kr
- 색인 대상 페르소나: 204개 (17지역 × 2성별 × 6연령구간)
- 기존 데이터 파일: `src/data/persona-stats.json` (페르소나별 통계 보유)
- 기존 페이지 라우터: `src/pages/persona/[...slug].astro`
- 현재 페이지에 이미 있는 것: 페르소나 인구통계, 추정 월소득, 8개 정부지원금 자동 매칭(복지로 데이터)

## 목적

현재 페르소나 페이지는 "당신은 이런 사람입니다" + "받을 수 있는 복지 목록"까지만 보여준다. 여기에 **"이 페르소나가 자격 대상이지만 실제로는 놓치고 있는 정부 지원금 TOP 3"** 섹션을 자동 생성으로 추가한다.

이 섹션의 핵심 차별점:
1. 모든 숫자가 공공데이터 기반 1차 통계 (LLM이 만든 추정치 금지)
2. 페르소나마다 결과가 통계적으로 다르게 도출됨
3. "내가 받을 수 있는 정부 지원금" 검색 의도에 직접 답하는 형태
4. AI Overview/SGE에 인용될 수 있도록 구체 숫자 + 출처 명시

**LLM은 데이터를 만들지 않는다. LLM은 이미 계산된 숫자를 문장으로 풀어 쓰는 데만 사용한다.**

## 작업 범위 (3단계)

### Phase 1: 데이터 파이프라인 구축 (가장 중요)

`scripts/build-decision-cards.ts` (또는 `.mjs`) 파일을 신규 생성. 이 스크립트는 빌드 전에 실행되어 `src/data/decision-cards.json`을 생성한다.

**입력 데이터 소스 (전부 공공/공개 데이터):**

1. **복지로(bokjiro.go.kr)** — 각 지원금의 자격 기준, 금액, 신청 방법
   - API가 있으면 API, 없으면 사전 수집된 JSON
   - 위치: `src/data/welfare-programs.json` (없으면 생성)
   - 필수 필드: `id`, `name`, `agency`, `eligibility_age_min`, `eligibility_age_max`, `eligibility_gender`, `eligibility_region`, `eligibility_income_max`, `eligibility_marital`, `amount_monthly`, `amount_annual`, `application_method`, `deadline`, `source_url`

2. **통계청 KOSIS 사회조사 / 복지패널** — 각 복지의 인지도와 신청률
   - 위치: `src/data/welfare-uptake-rates.json` (수동 큐레이션)
   - 필수 필드: `welfare_id`, `awareness_rate`, `eligible_rate_by_persona`, `application_rate_among_eligible`, `actual_receipt_rate`, `source`, `survey_year`
   - 데이터가 없는 복지는 보수적 추정치 사용 — **단, 추정치는 반드시 `is_estimated: true` 플래그로 표시**

3. **국세청 근로장려금/자녀장려금 수령 통계** — 자격 대상자 대비 실수령자 비율

4. **각 지자체 예산 소진율** (선택적, 데이터 있을 때만)

**계산 로직 (각 페르소나마다 반복):**

```typescript
interface Persona {
  region: string;       // "서울", "경기" 등 17개
  gender: '남자' | '여자';
  ageGroup: '20대' | '30대' | '40대' | '50대' | '60대' | '70대이상';
  estimatedIncome: number;  // 기존 persona-stats.json에서
  maritalRate: number;      // 기존 데이터
}

interface DecisionCard {
  rank: 1 | 2 | 3;
  welfare_id: string;
  welfare_name: string;
  agency: string;
  
  // 핵심: 갭 분석
  eligible_rate: number;        // 이 페르소나의 자격 충족 비율 (%)
  application_rate: number;     // 자격자 중 실제 신청 비율 (%)
  miss_rate: number;            // eligible_rate × (1 - application_rate)
  
  // 금액 정보
  amount_monthly: number;
  amount_annual: number;
  
  // 출처
  source_url: string;
  source_label: string;
  data_year: number;
  is_estimated: boolean;
  
  // 추가 인사이트 (정해진 패턴 중 하나, LLM 호출 없음)
  top_miss_reason: string;  // 사전 큐레이션된 미신청 사유
  application_deadline?: string;
}

// 각 페르소나에 대해 TOP 3 선정 규칙:
// 1. 자격 조건(나이·성별·지역·소득) 매칭
// 2. miss_rate가 가장 높은 3개 선정
// 3. 동률일 경우 amount_annual이 큰 것 우선
```

**산출물:** `src/data/decision-cards.json`

```json
{
  "서울-남자-30대": {
    "personaKey": "서울-남자-30대",
    "cards": [
      { "rank": 1, "welfare_id": "...", ... },
      { "rank": 2, ... },
      { "rank": 3, ... }
    ],
    "generatedAt": "2026-06-04T...",
    "totalEligibleAnnual": 4800000
  },
  ...204개
}
```

**스크립트 실행 명령:**
- `package.json`의 `scripts`에 `"build:cards": "node scripts/build-decision-cards.mjs"` 추가
- `"build"` 스크립트를 `"npm run build:cards && astro build"`로 수정 — 빌드 전 항상 카드 데이터가 최신화되도록

### Phase 2: 페이지 컴포넌트 추가

`src/components/DecisionCards.astro` 신규 생성:

```astro
---
interface Props {
  personaKey: string;
}
const { personaKey } = Astro.props;

import cardsData from '../data/decision-cards.json';
const personaCards = cardsData[personaKey];

if (!personaCards) return null;

const { cards, totalEligibleAnnual } = personaCards;
---

{cards && cards.length > 0 && (
  <section class="decision-cards" aria-label="이 페르소나가 놓치는 정부 지원금">
    <header>
      <h2>이 페르소나가 자주 놓치는 정부 지원금 TOP 3</h2>
      <p class="subtitle">
        자격 조건을 충족하지만 실제 신청률이 낮은 지원금 — 
        연 최대 <strong>{(totalEligibleAnnual / 10000).toFixed(0)}만원</strong> 추가 수령 가능
      </p>
    </header>

    {cards.map((card) => (
      <article class="decision-card" data-rank={card.rank}>
        <header class="card-header">
          <span class="rank-badge">#{card.rank}</span>
          <h3>{card.welfare_name}</h3>
          <span class="agency">{card.agency}</span>
        </header>

        <div class="gap-analysis">
          <div class="stat">
            <span class="stat-label">이 페르소나 중 자격 대상</span>
            <span class="stat-value">{card.eligible_rate}%</span>
          </div>
          <div class="stat">
            <span class="stat-label">자격자 중 실제 신청</span>
            <span class="stat-value">{card.application_rate}%</span>
          </div>
          <div class="stat highlight">
            <span class="stat-label">놓치고 있는 비율</span>
            <span class="stat-value">{card.miss_rate}%</span>
          </div>
        </div>

        <div class="amount">
          월 <strong>{(card.amount_monthly / 10000).toFixed(0)}만원</strong> · 
          연 <strong>{(card.amount_annual / 10000).toFixed(0)}만원</strong>
        </div>

        <p class="miss-reason">
          <strong>가장 흔한 미신청 사유:</strong> {card.top_miss_reason}
        </p>

        {card.application_deadline && (
          <p class="deadline">신청 마감: {card.application_deadline}</p>
        )}

        <footer class="card-footer">
          <a href={card.source_url} target="_blank" rel="noopener">
            {card.source_label} 신청 페이지 →
          </a>
          <span class="data-source">
            출처: {card.is_estimated ? '추정치' : `통계청 사회조사 ${card.data_year}`}
          </span>
        </footer>
      </article>
    ))}

    <!-- AI Overview/SGE 인용 최적화: 구조화 데이터 -->
    <script type="application/ld+json" set:html={JSON.stringify({
      "@context": "https://schema.org",
      "@type": "ItemList",
      "itemListElement": cards.map((card, idx) => ({
        "@type": "ListItem",
        "position": idx + 1,
        "name": card.welfare_name,
        "description": `${card.eligible_rate}%가 자격 대상이지만 ${card.application_rate}%만 신청. 월 ${card.amount_monthly}원.`
      }))
    })}></script>
  </section>
)}

<style>
  /* Tailwind v4 + 기존 사이트 톤에 맞춰 작성 */
  /* 카드 스타일은 기존 페이지의 "8개 정부지원금 매칭" 섹션과 시각적 일치성 유지 */
</style>
```

### Phase 3: 페이지에 컴포넌트 삽입

`src/pages/persona/[...slug].astro`를 수정해 기존 "정부지원금 매칭" 섹션 **바로 아래에** `<DecisionCards>` 컴포넌트를 추가한다.

- `personaKey`는 슬러그에서 추출 (예: 슬러그가 `서울-남자-30대`면 그대로 사용)
- 1년 단위 페르소나(예: `서울-남자-35`)에는 표시하지 않음 — `is10YearGroup` 체크
- 데이터가 없는 페르소나는 컴포넌트가 자동으로 null 반환 (위 코드에 처리됨)

## 데이터 시드 (Phase 1 보조)

ETL 스크립트를 처음 돌릴 때 실제 데이터가 없으면 빌드가 실패하므로, **다음 3개 시드 파일을 먼저 생성**한다:

### `src/data/welfare-programs.json` (시드 — 최소 15개)

다음 복지부터 우선 포함 (전국 단위 + 검색 수요 높음):
- 근로장려금 (국세청)
- 자녀장려금 (국세청)
- 청년월세 특별지원 (국토부)
- K-패스 (국토부)
- 국민내일배움카드 (고용부)
- 청년도약계좌 (금융위)
- 청년수당 (지자체별, 서울/경기/부산 우선)
- 부모급여 (보건복지부)
- 아동수당 (보건복지부)
- 첫만남이용권 (보건복지부)
- 긴급복지지원 (보건복지부)
- 기초연금 (보건복지부)
- 노인일자리 (보건복지부)
- 에너지바우처 (산업부)
- 주거급여 (국토부)

각 항목은 위에 정의한 인터페이스 필드를 모두 채울 것. **데이터는 2025년 기준 공개된 공식 정보를 사용하되, 출처 URL을 반드시 포함**한다.

### `src/data/welfare-uptake-rates.json` (시드)

- 통계청 사회조사, 복지패널, 국세청 통계연보에서 추출
- 데이터 없으면 `is_estimated: true`로 표시하고 보수적 추정치 사용

### `src/data/miss-reasons.json` (시드)

각 복지마다 가장 흔한 미신청 사유 1줄. 예:
```json
{
  "근로장려금": "소득 기준을 잘못 알고 있어서 신청 자체를 시도하지 않음",
  "청년월세특별지원": "보증금 기준(5천만원 이하)을 모르고 본인은 해당 안 된다고 단정",
  "K-패스": "전월 15회 이상 이용 조건을 충족하면서도 카드 신청을 미룸",
  ...
}
```

## 검증 명령

작업 완료 후 다음을 순서대로 실행:

```bash
# 1. 데이터 빌드
npm run build:cards

# 2. 생성된 데이터 검증
node -e "
const data = require('./src/data/decision-cards.json');
const keys = Object.keys(data);
console.log('총 페르소나 수:', keys.length);
console.log('예상: 204');
console.log('샘플 (서울-남자-30대):', JSON.stringify(data['서울-남자-30대'], null, 2));
"

# 3. Astro 풀 빌드
npm run build

# 4. 빌드된 페이지에 결정 카드 섹션이 들어갔는지 확인
grep -c "이 페르소나가 자주 놓치는" dist/persona/서울-남자-30대/index.html
# 기대값: 1 이상

# 5. 구조화 데이터(JSON-LD)가 박혔는지
grep -c "ItemList" dist/persona/서울-남자-30대/index.html
# 기대값: 1 이상

# 6. 1년 단위 페이지에는 들어가지 않아야 함
grep -c "이 페르소나가 자주 놓치는" dist/persona/서울-남자-35/index.html
# 기대값: 0
```

## 작업 후 보고할 것

1. 생성된 파일 목록과 각 파일의 라인 수
2. `decision-cards.json`의 페르소나 수 (204 기대)
3. `welfare-programs.json`에 포함된 복지 프로그램 수와 목록
4. `npm run build` 성공 여부 + 빌드 시간
5. 위 검증 명령 4·5·6번의 출력
6. 샘플 페르소나 3개의 결정 카드 데이터 전문 (서울-남자-30대, 부산-여자-60대, 제주-남자-40대)

## 절대 하지 말 것

- **LLM API 호출로 본문 텍스트를 생성하지 말 것.** 모든 문장은 정해진 템플릿에 데이터를 끼워 넣는 방식으로만 생성.
- 추정치를 실제 통계처럼 표기하지 말 것. `is_estimated: true`인 경우 UI에 명시.
- 기존 페르소나 페이지의 다른 섹션 수정 금지.
- 새 외부 패키지 설치 금지 (이미 설치된 패키지만 사용).
- `astro.config.mjs` 수정 금지.
- 1년 단위 페르소나 페이지에 결정 카드 추가 금지.

## 데이터 수집이 막힐 경우

복지로 API나 통계청 데이터 접근이 어려우면, **먼저 15개 복지에 대해 수동 큐레이션 JSON으로 시작**한다. 자동 크롤링은 v2로 미룬다. 핵심은 **데이터 파이프라인의 구조를 먼저 만드는 것**이지, 데이터 양이 아니다.

데이터 출처는 다음 우선순위로 확인:
1. 복지로 공식 사이트 (https://www.bokjiro.go.kr)
2. 각 부처 공식 보도자료
3. 통계청 KOSIS (https://kosis.kr)
4. 국세청 국세통계연보

수치를 만들어내지 말고, 출처가 확인되지 않으면 `is_estimated: true`로 명시할 것.
이 플랜을 구현할 수 있는지 확인해줘
- 작업 지시 (최종판): 페르소나 페이지에 "적합 지원금 결정 카드" 시스템 구축

## 컨텍스트

- 프로젝트 경로: `/Users/twinssn/Projects/money-aikorea24`
- 스택: Astro 6.1.8 (`output: 'static'`) + Cloudflare Pages
- 라이브 도메인: https://persona.aikorea24.kr
- 색인 대상: 204개 페르소나 (1년 단위는 noindex)

## 이미 존재하는 자산 (사전 분석으로 확인됨)

- `public/persona-stats.json` — 페르소나별 통계 ⚠️ `src/data/`가 아니라 `public/`에 있음
- `src/data/benefits-curated.json` — 큐레이션된 복지 24개 (금액 필드 없음)
- `src/data/welfare-central.json` — 중앙부처 복지 416개 (금액 필드 없음)
- `src/data/welfare-local.json` — 지자체 복지 4,565개 (금액 필드 없음)
- `src/lib/welfareMatcher.ts` — 페르소나 ↔ 복지 매칭 로직 (재사용)
- `src/pages/persona/[...slug].astro` — 페르소나 페이지 라우터

## 데이터 현실 (이전 설계에서 폐기한 것)

이전 설계는 다음 가정에 의존했으나 사실이 아님:
- ❌ "복지 데이터에 amount_annual 필드가 있다" — 5,000개 모두 금액 필드 없음
- ❌ "성별 필터링이 작동한다" — benefits-curated.json의 sex 필드가 대부분 비어있음
- ❌ "신청률 통계가 공개되어 있다" — 페르소나 단위 신청률은 비공개 데이터

따라서 다음 원칙으로 재설계:
- ✅ 금액 데이터는 **소수의 핵심 복지에 수동 큐레이션**부터 시작 (Stage 0A)
- ✅ 성별 필터 제외, 지역 + 연령 + 생애주기로만 매칭
- ✅ 추정치·신청률·갭 분석 일체 금지
- ✅ LLM 본문 생성 일체 금지

## 작업 범위 — 4단계로 분할

이 작업은 한 번에 다 하지 말고 **Stage 0A → Stage 0B → 보고 → 사용자 승인 → Stage 0C → Phase 1·2·3** 순서로 진행한다. Stage 0A부터 시작하고, 끝나면 결과를 보고한 후 사용자 승인을 받고 다음 단계로 진행한다.

---

### Stage 0A: 핵심 10개 복지에 금액 컬럼 추가 (최우선)

**대상 복지 (검색량·매칭 빈도 기준):**

1. 근로장려금 (국세청)
2. 자녀장려금 (국세청)
3. 청년월세 특별지원 (국토부)
4. K-패스 (국토부)
5. 국민내일배움카드 (고용부)
6. 청년도약계좌 (금융위)
7. 부모급여 (보건복지부)
8. 아동수당 (보건복지부)
9. 기초연금 (보건복지부)
10. 주거급여 (국토부)

**작업 내용:**

`src/data/benefits-curated.json`의 위 10개 항목에 다음 필드를 추가:

```json
{
  "amount_monthly": 250000,
  "amount_annual": 3000000,
  "amount_min_monthly": 100000,
  "amount_max_monthly": 400000,
  "amount_notes": "가구 형태에 따라 차등 — 단독가구 월 100,000, 4인가구 월 400,000",
  "amount_source_url": "https://www.bokjiro.go.kr/...",
  "amount_verified_date": "2026-06-04",
  "amount_year": 2025
}
```

**중요 원칙:**

- 금액은 2025년 기준 공식 발표값을 사용 (각 부처 보도자료 또는 복지로 확인)
- 범위가 있는 복지는 `amount_min`/`amount_max`로, 대표값을 `amount_monthly`/`amount_annual`로 (대표값은 중위 가구 기준)
- 출처 URL을 반드시 명시 (`amount_source_url`)
- **확인할 수 없는 숫자는 절대 추정하지 말 것.** 모르면 `null`로 두고 보고할 것.

**대상 복지가 benefits-curated.json에 없는 경우:**

해당 복지를 `welfare-central.json` 또는 `welfare-local.json`에서 찾아 `benefits-curated.json`으로 이동시키되, 원본 다른 파일은 그대로 둔다.

**보고할 것:**

1. 10개 중 금액을 채운 것 몇 개, null로 둔 것 몇 개
2. null로 둔 경우 그 이유 (예: "공식 자료에서 금액을 명시하지 않음")
3. 각 복지의 amount_source_url 목록
4. 변경된 benefits-curated.json의 diff 요약

**Stage 0A 완료 후 멈춤. 다음 단계 진행 전에 사용자 승인 대기.**

---

### Stage 1: 빌드 데이터 생성 (Stage 0A 승인 후)

`src/data/decision-cards.json`을 생성하는 로직을 구현한다.

**구현 위치:** 별도 빌드 스크립트가 아니라 **Astro 컴포넌트의 frontmatter** 또는 **`src/lib/` 안의 TS 모듈**로 구현한다. TypeScript ↔ Node 호환 문제 회피.

권장 구조:

```typescript
// src/lib/buildDecisionCards.ts
import benefitsCurated from '../data/benefits-curated.json';
import { matchPersonaToWelfare } from './welfareMatcher';
// persona-stats.json은 public/에 있으므로 fetch 또는 fs.readFileSync로 빌드 타임에 로드

export function buildAllDecisionCards() {
  const personas = loadPersonas();  // 204개
  const allWelfares = benefitsCurated;  // 우선 24개만
  
  const result = {};
  
  for (const persona of personas) {
    const matched = allWelfares
      .map(w => ({
        welfare: w,
        score: matchPersonaToWelfare(persona, w, { skipGenderFilter: true })
      }))
      .filter(m => m.score > 0);  // 매칭 안 된 것 제외
    
    const totalEligibleAnnual = matched
      .filter(m => m.welfare.amount_annual && m.welfare.amount_annual > 0)
      .reduce((sum, m) => sum + m.welfare.amount_annual, 0);
    
    const withAmountCount = matched.filter(m => m.welfare.amount_annual > 0).length;
    
    // TOP 3 선정: 금액 있는 것 우선, 그다음 점수
    const topThree = matched
      .sort((a, b) => {
        const aHasAmount = (a.welfare.amount_annual || 0) > 0 ? 1 : 0;
        const bHasAmount = (b.welfare.amount_annual || 0) > 0 ? 1 : 0;
        if (aHasAmount !== bHasAmount) return bHasAmount - aHasAmount;
        return b.score - a.score;
      })
      .slice(0, 3);
    
    result[persona.key] = {
      personaKey: persona.key,
      totalMatchedCount: matched.length,
      withAmountCount,                  // 금액 정보 있는 것 몇 개
      totalEligibleAnnual,              // 0일 수 있음 (그땐 UI에서 숨김)
      topThree: topThree.map(m => ({
        welfare_id: m.welfare.id || m.welfare.name,
        welfare_name: m.welfare.name,
        agency: m.welfare.org || m.welfare.agency,
        amount_monthly: m.welfare.amount_monthly || null,
        amount_annual: m.welfare.amount_annual || null,
        amount_notes: m.welfare.amount_notes || null,
        eligibility_summary: m.welfare.target || m.welfare.purpose || '',
        application_method: m.welfare.method || '',
        source_url: m.welfare.url || m.welfare.amount_source_url || '',
        source_label: m.welfare.amount_source_url ? '복지로/공식' : '큐레이션',
        score: m.score
      })),
      generatedAt: new Date().toISOString()
    };
  }
  
  return result;
}
```

**중요:**
- `matchPersonaToWelfare`에 `{ skipGenderFilter: true }` 옵션을 전달 (성별 필터 비활성)
- 만약 `welfareMatcher.ts`에 해당 옵션이 없으면 추가하되 **기존 로직은 절대 수정하지 않음** (옵션이 false면 원래 동작)

**실행 방식 결정:**

빌드 타임에 한 번만 실행하려면 두 가지 선택지:

**선택지 A (권장):** Astro의 `getStaticPaths` 안에서 `buildAllDecisionCards()`를 호출하고 props로 각 페이지에 전달.

**선택지 B:** 별도 파일 `src/data/decision-cards.json`을 생성하는 prebuild 스크립트. 단, `tsx` 패키지 설치 없이 가능한 방법으로 (예: Astro의 `astro sync` 활용 또는 컴포넌트 안에서 직접 처리).

**가장 단순한 길은 A.** 별도 JSON 파일을 만들지 않고 빌드 타임에 직접 계산. 204개 페르소나 × 24개 복지 = 4,896 매칭이라 계산량도 작음.

---

### Stage 2: 컴포넌트 (Stage 1 완료 후)

`src/components/DecisionCards.astro` 생성:

```astro
---
import type { DecisionCardData } from '../lib/buildDecisionCards';

interface Props {
  data: DecisionCardData;  // 페이지에서 props로 받음
}
const { data } = Astro.props;

if (!data || !data.topThree || data.topThree.length === 0) {
  return null;
}

const { totalMatchedCount, withAmountCount, totalEligibleAnnual, topThree } = data;
const showAnnualSummary = totalEligibleAnnual > 0;
const totalAnnualMan = showAnnualSummary ? Math.floor(totalEligibleAnnual / 10000) : 0;
---

<section class="decision-cards">
  <header>
    <h2>이 페르소나에게 가장 적합한 정부 지원금 TOP 3</h2>
    <p class="summary">
      자격 조건 매칭 <strong>{totalMatchedCount}개</strong>
      {showAnnualSummary && (
        <> · 금액 확인된 항목 합산 연 최대 <strong>{totalAnnualMan.toLocaleString()}만원</strong></>
      )}
    </p>
    <p class="data-note">
      복지로 공식 데이터 기준 · 지역·연령·생애주기로 자동 필터링
      {withAmountCount < totalMatchedCount && (
        <> · 금액 정보가 확인되지 않은 항목은 합계에서 제외</>
      )}
    </p>
  </header>

  {topThree.map((card, idx) => (
    <article class="decision-card">
      <header>
        <span class="rank">#{idx + 1}</span>
        <div>
          <h3>{card.welfare_name}</h3>
          <span class="agency">{card.agency}</span>
        </div>
      </header>

      {(card.amount_annual || card.amount_monthly) && (
        <div class="amount-box">
          {card.amount_monthly && (
            <span>월 <strong>{(card.amount_monthly / 10000).toFixed(0)}만원</strong></span>
          )}
          {card.amount_annual && (
            <span>연 최대 <strong>{(card.amount_annual / 10000).toFixed(0)}만원</strong></span>
          )}
          {card.amount_notes && (
            <p class="amount-notes">{card.amount_notes}</p>
          )}
        </div>
      )}

      {card.eligibility_summary && (
        <div class="eligibility">
          <strong>이런 분께 추천합니다:</strong>
          <p>{card.eligibility_summary}</p>
        </div>
      )}

      {card.application_method && (
        <div class="application">
          <strong>신청:</strong> {card.application_method}
        </div>
      )}

      {card.source_url && (
        <a href={card.source_url} target="_blank" rel="noopener">
          공식 페이지 확인 →
        </a>
      )}
    </article>
  ))}

  <script type="application/ld+json" set:html={JSON.stringify({
    "@context": "https://schema.org",
    "@type": "ItemList",
    "itemListElement": topThree.map((card, idx) => ({
      "@type": "ListItem",
      "position": idx + 1,
      "name": card.welfare_name,
      "description": [
        card.agency,
        card.amount_annual ? `연 최대 ${Math.floor(card.amount_annual / 10000)}만원` : null,
        card.eligibility_summary
      ].filter(Boolean).join(' · ')
    }))
  })}></script>
</section>

<style>
  /* 기존 "8개 정부지원금 매칭" 섹션과 시각적 일관성. Tailwind v4 유틸 우선 */
</style>
```

---

### Stage 3: 페이지 삽입 (Stage 2 완료 후)

`src/pages/persona/[...slug].astro` 수정:

```astro
---
import { buildAllDecisionCards } from '../../lib/buildDecisionCards';
import DecisionCards from '../../components/DecisionCards.astro';

export async function getStaticPaths() {
  const allCards = buildAllDecisionCards();
  // 기존 페르소나 페이지 생성 로직에 decisionCardData를 props로 추가
  return personas.map(p => ({
    params: { slug: p.slug },
    props: { 
      persona: p, 
      decisionCardData: allCards[p.key] || null,
      // ...기타 기존 props
    }
  }));
}

const { persona, decisionCardData } = Astro.props;
const isYearlyPersona = /^\d+$/.test(ageSegment);
---

<!-- 기존 8개 정부지원금 매칭 섹션 -->
<!-- ... -->

{!isYearlyPersona && decisionCardData && (
  <DecisionCards data={decisionCardData} />
)}
```

---

## 검증 명령 (Stage 3 완료 후)

```bash
# 1. 풀 빌드
npm run build

# 2. 결정 카드 섹션이 들어갔는지
grep -c "이 페르소나에게 가장 적합한" dist/persona/서울-남자-30대/index.html

# 3. JSON-LD 인용 데이터
grep -c "ItemList" dist/persona/서울-남자-30대/index.html

# 4. 1년 단위 페이지에는 없어야 함
grep -c "이 페르소나에게 가장 적합한" dist/persona/서울-남자-35/index.html

# 5. 금액 정보가 페이지에 노출되는지
grep -oE '연 최대 [0-9,]+만원' dist/persona/서울-남자-30대/index.html | head -5

# 6. 여러 페르소나 샘플의 결정 카드가 서로 다른지 확인
for p in "서울-남자-30대" "부산-여자-60대" "제주-여자-70대이상" "세종-남자-40대"; do
  echo "=== $p ==="
  grep -oE '<h3>[^<]+</h3>' "dist/persona/$p/index.html" | head -5
done
```

---

## 최종 보고할 것 (각 Stage 완료마다)

**Stage 0A 완료 시:**
- 10개 복지 중 금액 채운 수 / null 둔 수
- amount_source_url 목록
- 각 복지의 amount_monthly / amount_annual 요약

**Stage 1 완료 시:**
- 204개 페르소나 중 매칭된 페르소나 수, 매칭 0개 페르소나 목록
- 평균 매칭 복지 수, 평균 withAmountCount
- 샘플 3개 페르소나 (서울-남자-30대, 부산-여자-60대, 제주-여자-70대이상)의 decisionCardData 전문

**Stage 2 완료 시:**
- DecisionCards.astro 파일과 라인 수
- 시각 디자인이 기존 8개 지원금 카드와 일관성 있는지

**Stage 3 완료 시:**
- npm run build 시간
- 위 검증 명령 1~6번 출력

---

## 절대 금지

- LLM API 호출로 본문 생성
- 추정치 통계 (신청률·인지도·갭 등) 생성
- 확인 불가능한 금액을 추정해서 입력
- 새 패키지 설치 (`tsx`, `ts-node` 등 포함)
- `astro.config.mjs` 수정
- 1년 단위 페르소나에 결정 카드 추가
- `welfareMatcher.ts` 기존 로직 수정 (옵션 추가만 허용)
- Stage 0A 완료 전에 Stage 1로 진행
- 한 번에 모든 Stage 실행
