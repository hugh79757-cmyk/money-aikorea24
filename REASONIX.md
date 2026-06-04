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
