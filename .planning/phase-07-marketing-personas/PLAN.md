---
phase: 07-marketing-personas
plan: 01
type: execute
wave: 1
requirements: [MKT-01, MKT-02, MKT-03, MKT-04, MKT-05]
depends_on: []
autonomous: true
files_modified:
  - migrations/0002_marketing_usage.sql
  - functions/api/marketing/persona.js
  - functions/api/marketing/_shared/llm.js
  - src/pages/marketing-persona.astro
must_haves:
  truths:
    - "미로그인 방문자가 페르소나 프로파일(통계 카드)을 열람할 수 있다"
    - "미로그인이 생성 버튼을 누르면 카카오 로그인 유도가 표시된다"
    - "로그인 사용자가 product-first와 persona-first 양쪽 모두에서 LLM 생성 결과를 받는다"
    - "생성 결과가 드림 고객 시트(F1~F9)로 강제되며, 누락 시 재생성→폴백 회전이 작동한다"
    - "결과가 프로필 카드+세로 타임라인+검색창 목업+복사/인쇄 시트로 렌더링된다"
    - "일일 5회 초과 사용자는 429로 차단된다"
  artifacts:
    - path: migrations/0002_marketing_usage.sql
      provides: marketing_usage D1 테이블
      contains: "CREATE TABLE IF NOT EXISTS marketing_usage"
    - path: functions/api/marketing/persona.js
      provides: 인증 게이트 + 일일 한도 + LLM 프록시
      exports: ["onRequestPost"]
    - path: functions/api/marketing/_shared/llm.js
      provides: 폴백 체인 + F1-F9 검증 게이트
      exports: ["generateScenario"]
    - path: src/pages/marketing-persona.astro
      provides: 양방향 UI + 드림 고객 시트 시각화
  key_links:
    - from: src/pages/marketing-persona.astro
      to: functions/api/marketing/persona.js
      via: POST fetch {mode, product|personaKey}
      pattern: "fetch\\('/api/marketing/persona'"
    - from: functions/api/marketing/persona.js
      to: functions/api/_shared/session.js
      via: getSession 인증 게이트
      pattern: "getSession"
    - from: src/pages/marketing-persona.astro
      to: public/persona-stats-decade.json
      via: 런타임 fetch (my-persona.astro 선례)
      pattern: "persona-stats-decade\\.json"
---

# PLAN: Phase 7 Marketing Persona Studio

> 단일 실행 플랜. 작업 항목 순서: **A → B∥C → D → E**. 신규 파일만 추가(additive only), 기존 파일 수정·시그니처 변경 없음.

## 근거 문서

- 요구사항 단일 출처: `@.planning/phase-07-marketing-personas/CONTEXT.md` (MKT-01..05, A-1..A-5, 성공기준 1-7)
- 실측: `@.planning/phase-07-marketing-personas/RESEARCH.md`
- 제약: `@AGENTS.md` (static output, Pages Functions, AdSense 계열 매핑 — 이 페이지는 **ca-pub-5938862195544185(aikorea24)만**)

## 플래너가 해소한 가정 (CONTEXT.md A-1..A-5 범위 내 결정)

| # | 질문 | 결정 | 이유 |
|---|------|------|------|
| R-1 | product-first 역매칭 구현 방식 | 별도 역매칭 코드 미작성. **단일 LLM 호출**로 제품 설명 → 매칭 페르소나(지역·성별·연령대·소득) 생성. benefitMatcher.ts의 어휘(연령대·지역 조건 표현)를 프롬프트 지시에 반영 | MKT-02는 "매칭된 페르소나 출력"을 요구하지 알고리즘을 지정하지 않음. 204키 후보 나열은 컨텍스트 한계 |
| R-2 | persona-first 서버 데이터 | 서버는 `personaKey`만 받아 파싱. 클라이언트가 `/persona-stats-decade.json`(4MiB) 직접 fetch해 프로파일 표시(my-persona.astro 선례). **열람은 비로그인 허용**(MKT-01) | 서버 부하·응답 크기 절약. 통계 열람 자체가 공개 요구사항 |
| R-3 | 한도 차감 시점 | LLM 호출 **전** 증분(reserve). 실패한 생성도 1회 소비. refund 없음 | 동시 요청 봉쇄 우선. refund는 YAGNI(A-4 정신 준용) |
| R-4 | 모델 체인 (MKT-03 "최소 2~3") | 3단계: nvidia `google/diffusiongemma-26b-a4b-it` → deepseek `deepseek-chat` → nvidia `meta/llama-3.1-8b-instruct` | **2026-08-23 실측 재편성**: 구 2순위 gemma-3n-e4b-it은 410 Gone(EOL), gemma-4-31b-it은 90초 무응답 확인 → 제거. 현 체인 3모델 전부 당일 200 OK 실측. 유료 최후폴백 원칙상 free nvidia/deepseek 우선 |
| R-5 | 일일 한도 기준일 | UTC 일자(`new Date().toISOString().slice(0,10)`) | KST 보정 YAGNI. 남용 방지 목적상 UTC 충분 |
| R-6 | AdSense 슬롯 값 | `data-ad-slot="auto"` — my-persona.astro 기존 검증 패턴 복사 | 같은 계정에서 운영 중 패턴. 콘솔 수동 작업 불필요 |
| R-7 | F1-F9 JSON 표현 | 최상위 객체 `{f1,f2,f3,f4,f5,f6,f7,f8,f9}`. f3=f3개 문장 배열, f9=2~3개 배열, f8=`{current,change,role,next}` 4키 객체(각 2~3문장), 나머지=문자열 | MKT-04 테이블의 1:1 직역. 렌더러(D)가 소비하는 계약 |
| R-8 | F3 카테고리어 휴리스크 구체화 | 각 문장: (a) 8자 이상 60자 이하, (b) 조사·고민어 휴리스크 정규식 `/[은는이가을를에서]|어떻게|어디|얼마|방법|추천|비교|할까|해야|고민/` 1개 이상 일치. 미일치 문장 1개라도 있으면 게이트 실패 | CONTEXT MKT-04 "길이·조사 패턴 휴리스틱"의 실행 가능한 정의. 반례 "정통 사주 분석"(7자, 조사 없음)은 두 조건 모두 탈락 |

---

## 작업 항목 A — API 골격: 인증 게이트 + D1 일일 한도 (MKT-01, A-3)

**파일**: `migrations/0002_marketing_usage.sql` (신규), `functions/api/marketing/persona.js` (신규)

### 태스크

**A-1. D1 마이그레이션** — `migrations/0002_marketing_usage.sql` 생성 (기존 migration 컨벤션 준수):

```sql
CREATE TABLE IF NOT EXISTS marketing_usage (
  user_id TEXT NOT NULL,
  day TEXT NOT NULL,
  count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
);
```

적용 (글로벌 AGENTS.md 규칙 — wrangler 앞 `env -u CLOUDFLARE_API_TOKEN`):

```bash
env -u CLOUDFLARE_API_TOKEN npx wrangler d1 execute persona-db --local --file migrations/0002_marketing_usage.sql
env -u CLOUDFLARE_API_TOKEN npx wrangler d1 execute persona-db --remote --file migrations/0002_marketing_usage.sql
```

**A-2. `functions/api/marketing/persona.js` — LLM 호출부 제외한 전체 파이프라인**

구조는 `functions/api/benefit-click.js` 선례 준수 (corsHeaders + `onRequestOptions` 204 + `ALLOWED_ORIGIN='https://persona.aikorea24.kr'`). `onRequestPost({ request, env })` 처리 순서:

1. body JSON 파싱 + 입력 검증. `mode`는 `'product'` | `'persona'`. product 모드: `product` 비공백 문자열, 최대 2,000자. persona 모드: `personaKey`가 `/^.{1,20}_(남자|여자)_(10|20|30|40|50|60|70|80)대$/u` 일치 (예: `서울_여자_30대`). 위반 시 400 `{error:'bad_request'}`
2. **인증 게이트**: `import { getSession } from '../_shared/session.js'` → `getSession(request, env)` null이면 401 `{error:'login_required'}`. 세션 페이로드의 `id`(callback/kakao.js 확인됨)를 user_id로 사용
3. **일일 한도**(A-3, 기본 5): `day`=UTC 오늘(R-5). `SELECT count FROM marketing_usage WHERE user_id=? AND day=?` → count ≥ 5면 429 `{error:'rate_limited', remaining:0}`. 미달이면 benefit-click.js와 동일한 `INSERT ... ON CONFLICT(user_id,day) DO UPDATE SET count=count+1` upsert로 **호출 전 예약**(R-3)
4. `generateScenario({mode, product, personaKey})` 호출 — 이 항목에서는 `functions/api/marketing/_shared/llm.js`에 stub(`throw new Error('NOT_IMPLEMENTED')`)만 두고 catch하여 502 `{error:'generation_failed'}` 반환. B에서 실구현 교체
5. 성공 시(B 이후): 200 `{ok:true, scenario, model_used}` — scenario는 R-7 JSON 구조
6. 전체 try/catch → 500 `{error:'internal'}`. 콘솔 로그에 API 키·세션 토큰 문자열 절대 출력 금지

### Verification

```bash
npm run build && (npx wrangler pages dev &)   # 로컬 Functions + 로컬 D1
# 1. 미로그인 → 401
curl -s -X POST localhost:8788/api/marketing/persona -d '{"mode":"persona","personaKey":"서울_여자_30대"}'
#    기대: {"error":"login_required"}
# 2. 유효 세션(session.js createSessionToken과 동일 HMAC-SHA256 b64url 서명, SESSION_SECRET=.env) 쿠키로:
curl -s -X POST localhost:8788/api/marketing/persona -H "Cookie: session=$TOKEN" -d '{"mode":"bogus"}'
#    기대: 400 bad_request
curl -s -X POST localhost:8788/api/marketing/persona -H "Cookie: session=$TOKEN" -d '{"mode":"persona","personaKey":"서울_여자_30대"}'
#    기대: 502 generation_failed (stub)
env -u CLOUDFLARE_API_TOKEN npx wrangler d1 execute persona-db --local --command "SELECT * FROM marketing_usage"
#    기대: 해당 user_id 행 count=1
# 3. 동일 호출 반복 → 6번째부터 기대: 429 rate_limited
```

**완료 기준**: 401/400/502/429 경로 응답 실측 + marketing_usage 증분 확인.

---

## 작업 항목 B — LLM 폴백 체인 + 드림 고객 시트(F1-F9) 게이트 (MKT-03, MKT-04)

**파일**: `functions/api/marketing/_shared/llm.js` (신규, stub 교체), `functions/api/marketing/persona.js` (import 연결만)

**선행**: 작업 항목 A 완료.

### 태스크

**B-1. `_shared/llm.js` — writer.py 축소 이식 + MKT-04 스키마 강제**

- `MODEL_CHAIN` 상수 (R-4):

```js
const MODEL_CHAIN = [
  { provider:'nvidia',   model:'google/diffusiongemma-26b-a4b-it', keyEnv:'NVIDIA_API_KEY',     baseUrl:'https://integrate.api.nvidia.com/v1' },
  { provider:'nvidia',   model:'google/gemma-3n-e4b-it',           keyEnv:'NVIDIA_API_KEY',     baseUrl:'https://integrate.api.nvidia.com/v1' },
  { provider:'deepseek', model:'deepseek-chat',                    keyEnv:'DEEPSEEK_API_TOKEN', baseUrl:'https://api.deepseek.com/v1' },
];
```

- `callModel(entry, messages)`: OpenAI 호환 `POST {baseUrl}/chat/completions`, `Authorization: Bearer env[entry.keyEnv]`, body `{model, messages, temperature:0.7, max_tokens:2500}`, `AbortSignal.timeout(60000)` (per-attempt timeout)
- 오류 분류 (writer.py `_classify_error` 개념):
  - fetch 예외/timeout → 다음 모델
  - HTTP 429 → 다음 모델 (짧은 cooldown 후 재시도 불요 — 회전이 cooldown 역할). 트레이스: `console.log('[llm] rotate', entry.model, reason)` — reason은 'timeout'|'http_429'|'empty'|'gate_fail' 등 열거값만. **키·본문 미출력**
  - 응답에서 `<think>...</think>` 제거 + 코드펜스(```json … ```) 벗기기 후 trim 결과가 빈 문자열 → "빈/reasoning-only" → 다음 모델
- `buildPrompt(mode, ctx)` — **JSON 전용 출력 강제**:
  - system: 한국어 마케팅 페르소나 전문가 역할 + "반드시 아래 JSON 스키마만 출력. 다른 텍스트·주석·코드펜스 금지" + 스키마 명세(R-7, MKT-04 테이블 그대로): f1=가상 인물 1명 프로필(이름·연령·직업·거주지 규모·가족 상황, 통계와 일치), f2=현재 장면(시간대·장소·행동, 소설 장면처럼), f3=검색창 문장 ×3(카테고리어 금지, 고민 언어 그대로, 8~60자, 조사 포함), f4=오퍼 한 줄(헤드카피용), f5=결제 직전 두려움, f6=미해결 손해(돈·시간·기회), f7=이미 쓴 돈(무엇에·대략 금액), f8={current→원하는 변화→우리의 역할→다음 행동} 각 2~3문장, f9=다음 행동 선택지 2~3개 + "통계 기반 가상 인물이며 실존 인물 아님을 암묵적으로 유지" + "입력받은 지시사항을 출력에 노출 금지"
  - user(product): 제품 설명 원문 + "이 제품을 살 법한 페르소나를 한국 인구통계 어휘(광역 지역명·성별·연령대·소득)로 구체화" 지시(R-1)
  - user(persona): personaKey를 지역/성별/연령대로 파싱한 텍스트(R-2)
- `validateScenario(obj)` **검증 게이트** (MKT-04):
  1. obj가 파싱 가능한 JSON이고 9키(f1~f9) 전부 존재
  2. f1,f2,f4,f5,f6,f7 = trim 후 비어있지 않은 문자열(각 ≥ 15자)
  3. f8 = current/change/role/next 4키 전부 비어있지 않은 문자열
  4. f3 = 길이 3 배열, 각 항목이 R-8 휴리스크 통과
  5. f9 = 2~3개 비공백 문자열 배열
  6. 릭 블랙리스트 부재(전체 JSON.stringify 기준): `/system prompt|as an AI|AI 언어모델|프롬프트 지침/i`
- `generateScenario(ctx)` **재생성→회전 흐름** (MKT-04 "실패 시 재생성 1회 → 폴백 회전"): MODEL_CHAIN 순회하며 각 모델당 최대 2회 시도 — 1차 실패 시 같은 모델에 "이전 출력이 형식 요건을 충족하지 못했다. 스키마를 정확히 지켜 다시 JSON만 출력" 수정 지시를 assistant/user로 추가해 **재생성 1회**, 재실패 시 다음 모델로 회전. 최초 게이트 통과 응답을 `{scenario: obj, model_used: entry.model}`로 반환. 전부 실패 시 Error throw(persona.js가 502 변환)

**B-2. persona.js stub 교체** — `import { generateScenario } from './_shared/llm.js'`. 기존 401/400/429/500 경로·시그니처 무변경.

**B-3. Pages Secret 등록 (자동화)** — `.env` → `~/.env.common` 폴백에서 값 읽어 등록:

```bash
for K in NVIDIA_API_KEY DEEPSEEK_API_TOKEN; do
  grep -h "^$K=" .env ~/.env.common 2>/dev/null | head -1 | cut -d= -f2- \
    | env -u CLOUDFLARE_API_TOKEN npx wrangler pages secret put $K --project-name money-aikorea24
done
```

wrangler 인증 실패 시에만 사용자 대시보드 수동 등록 checkpoint로 전환(값은 기존 것 재사용, 신규 발급 불필요). 로컬 검증용 `.dev.vars`(같은 키 2개)는 에이전트가 생성하며, **`.gitignore`에 `.dev.vars` 1행 추가를 허용한다(CONFIG 변경, 동작 변경 아님 — W-1 반영)**. 추가 전 `git check-ignore .dev.vars`로 이미 무시되는지 먼저 확인(중복 등록 방지).

### Verification

```bash
# 로컬(.dev.vars 주입 wrangler pages dev):
# 1. 정상: 유효 세션 + mode=persona personaKey=서울_여자_30대 → 200,
#    scenario.f1~f9 존재, scenario.f3.length===3, Array.isArray(scenario.f9), f8 4키 존재
# 2. 회전: .dev.vars NVIDIA_API_KEY를 무효값 교체(DEEPSEEK 실값 유지) → model_used === 'deepseek-chat'
# 3. 게이트: curl 응답 scenario를 node -e 로 validateScenario 동등 체크 스크립트로 재검증 → pass
# 4. 트레이스: dev 콘솔 로그에 'nvapi-' 또는 'sk-' 접두 문자열 0건 (grep)
```

**완료 기준**: F1-F9 완전한 200 응답 실측 + 무효 키 시 폴백 모델 자동 전환(model_used) 실측 + 로그에 시크릿 0건.

---

## 작업 항목 C — 공개 페이지 `/marketing-persona`: 양방향 UI + 로그인 게이트 (MKT-01, MKT-02, A-1)

**파일**: `src/pages/marketing-persona.astro` (신규)

**선행**: 작업 항목 A(API 계약 확정). B와 병렬 가능(파일 교집합 없음).

### 태스크

**C-1. 페이지 골격 + SEO** — my-persona.astro 구조 선례: Layout + BaseHead(title/description/canonical=`persona.aikorea24.kr/marketing-persona`) + Header/Footer. Tailwind v4 유틸리티로 기존 페이지 톤 일치. `<noscript>` 안내 포함(생성 기능은 클라이언트 SPA).

**C-2. 양방향 탭 UI (MKT-02 — 양방향 모두 필수)** — 클라이언트 스크립트 탭 토글:

- **product-first 탭**: textarea(제품·서비스 설명, maxlength 2000, placeholder 예시 1개) + 생성 버튼
- **persona-first 탭**: 지역 버튼 그룹(index.astro REGIONS와 동일 짧은 이름 목록: 서울·경기·인천·부산·대구·광주·대전·울산·세종·강원·충북·충남·전북·전남·경북·경남·제주) + 성별(남자/여자) + 연령대(10대~80대) → `personaKey = \`${region}_${gender}_${decade}\`` 조립. 탭 진입 시 `fetch('/persona-stats-decade.json')` 1회(my-persona.astro 선례) → 선택 완료 시 해당 키 education/income/jobs 요약 카드 렌더. **이 프로파일 열람은 비로그인 허용**(MKT-01)
- **생성 버튼 공통 흐름**: `document.cookie`에서 `session_ui=` 파싱(Header.astro 패턴) → 없으면 카카오 로그인 유도 UI(`<a href="/auth/login">`, "카카오 로그인 후 AI 생성 가능 · 1일 5회") 표시하고 요청 차단. 있으면 `POST /api/marketing/persona` ({mode, product|personaKey})
- **응답 상태 처리**: 로딩 스피너 / 200 → 결과 렌더(D 렌더러 호출, B 완료 전에는 raw JSON pretty-print 임시 표시로 계약만 검증) / 401 → 로그인 유도 / 429 → "오늘 5회를 모두 사용했어요" / 502 → "생성에 실패했습니다. 잠시 후 다시 시도해 주세요."
- **XSS 방지**: `src/lib/html-sanitizer.ts`의 escape 함수 재사용. LLM 출력 raw innerHTML 삽입 금지
- **면책 문구**: 하단 "본 페르소나는 공공 통계 기반의 가상 인물이며 실존 인물이 아닙니다"(RESEARCH 리스크 메모)

Additive 원칙: 기존 파일 수정 없음(내비 링크 추가 등 발견성 작업은 본 플랜 범위 밖).

### Verification

```bash
npm run build   # 0 에러
```

브라우저(npm run dev):
1. `/marketing-persona` 접속 → 탭 2개 렌더
2. **비로그인** persona-first 선택 → 통계 프로파일 카드 표시 (열람 OK — 성공기준 1)
3. 비로그인 "생성" 클릭 → 로그인 유도 UI 표시, API 호출 없음
4. 로그인 후 product-first 입력 → (A만 있으면) 502 안내 표시 확인, (B 병합 후) 시트 렌더 확인

**완료 기준**: 빌드 0에러 + 1~3 브라우저 실측 통과.

---

## 작업 항목 D — 드림 고객 시트 시각화 (MKT-05)

**파일**: `src/pages/marketing-persona.astro` (C가 만든 파일에 렌더러 추가)

**선행**: 작업 항목 C. (B의 실응답 없어도 mock JSON으로 개발·검증 가능)

### 태스크

R-7 JSON을 받아 Tailwind v4로 렌더링하는 `renderDreamCustomerSheet(scenario)` 클라이언트 함수:

- **F1 프로필 카드**: 상단 히어로 카드 — 이름 크게 + 연령·직업·거주지·가족 배지 행. `public/cards/` JPG의 시각 언어(굵은 제목 + 카테고리 배지) 참조, CSS 렌더만(서버 이미지 생성 없음 — MKT-05 명시)
- **F2 현재 장면**: 인용 스타일 카드(border-l 강조, 이탤릭 유사체)
- **F3 검색창 목업 ×3**: 각 문장을 실제 검색창처럼 — 둥근 pill 컨테이너 + 좌측 돋보기 SVG + 회색 placeholder 톤 텍스트 + 우측 파란 검색 버튼 더미. 3개 세로 나열
- **F4 오퍼 한 줄**: 풀와이드 헤드카피 박스(큰 bold 텍스트, accent 배경)
- **F5/F6/F7 3열 카드 grid**(모바일 1열): 결제 직전 두려움 / 미해결 손해 / 이미 쓴 돈 — 각 카드 아이콘+제목+본문
- **F8 세로 타임라인 4단**: 좌측 수직 연결선 + 번호 원형 노드 4개(현재 장면→원하는 변화→우리의 역할→다음 행동). **3단 "우리의 역할" = 변화 포인트** 시각 강조 — accent 색 노드 링 + 배지("변화 포인트") + 배경 tint. 각 단계 카드에 해당 문장
- **F9 다음 행동 선택지**: 칩/버튼 리스트 2~3개 (번호 + 텍스트)
- **복사/인쇄 (단일 시트)**: (a) "시트 복사" 버튼 — F1~F9를 사람이 읽는 텍스트로 직렬화해 `navigator.clipboard.writeText`; (b) 인쇄 레이아웃 — `@media print` 블록에서 헤더/탭/버튼/AdSense `display:none`, 시트 컨테이너만 단일 컬럼 유지
- C의 응답 처리(200 분기)가 이 렌더기를 호출하도록 교체. escape 규칙(C-2) 동일 적용

### Verification

```bash
npm run build   # 0 에러
rg -c 'renderDreamCustomerSheet' src/pages/marketing-persona.astro   # ≥ 2 (정의+호출)
rg -c '변화 포인트' src/pages/marketing-persona.astro                # ≥ 1
rg -c '@media print' src/pages/marketing-persona.astro               # ≥ 1
rg -c 'navigator.clipboard' src/pages/marketing-persona.astro        # ≥ 1
```

브라우저: devtools 콘솔에서 mock 시나리오 JSON으로 `renderDreamCustomerSheet(mock)` 실행 → (1) F1 카드, (2) F3 검색창 목업 3개, (3) F8 타임라인 4노드+3단 강조, (4) 복사 버튼 → 클립보드에 F1~F9 텍스트, (5) 인쇄 미리보기에서 헤더/버튼 숨김 확인. **스크린샷 캡처**(성공기준 5 실측).

**완료 기준**: 빌드 0에러 + mock 데이터 5항목 렌더 실측 + 스크린샷 확보.

---

## 작업 항목 E — AdSense 슬롯 1개 (A-5, 선택·마지막)

**파일**: `src/pages/marketing-persona.astro` (결과 컨테이너 하단)

**선행**: 작업 항목 D.

### 태스크

- 로더 스크립트 **추가 금지** — BaseHead.astro가 이미 `ca-pub-5938862195544185` 클라이언트로 adsbygoogle.js 전역 로드. 이중 로드 = 중복 광고 요청
- 결과 컨테이너 하단에 my-persona.astro 검증 패턴 그대로 삽입(R-6):

```html
<ins class="adsbygoogle" style="display:block; width:100%; text-align:center"
     data-ad-client="ca-pub-5938862195544185"
     data-ad-slot="auto" data-ad-format="auto" data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
```

- push는 페이지 내 1회(guard 불필요). `@media print` 숨김 목록에 이 요소 포함(D에서 처리)
- **계열 규칙(글로벌 AGENTS.md)**: 이 페이지에 다른 ca-pub-* ID 절대 삽입 금지. 로더(BaseHead)와 data-ad-client 불일치 = 백지 광고

### Verification

```bash
npm run build   # 0 에러
rg -c 'data-ad-client="ca-pub-5938862195544185"' src/pages/marketing-persona.astro   # ≥ 1
rg -o 'ca-pub-[0-9]+' src/pages/marketing-persona.astro | sort -u                    # 5938862195544185 하나뿐
rg -c 'pagead2' src/pages/marketing-persona.astro                                    # 0건 (로더 중복 없음)
```

**완료 기준**: 빌드 0에러 + 페이지 내 ca-pub 문자열이 5938862195544185 하나임이 grep 실측.

---

## 실행 순서 / 웨이브

| 웨이브 | 항목 | 근거 |
|--------|------|------|
| 1 | A | API 계약(응답 코드·바디·scenario JSON 구조) 확정 — B·C 선행 |
| 2 | B ∥ C | 파일 교집합 없음(llm.js+persona.js vs astro 페이지). 계약은 A로 고정 |
| 3 | D | C가 만든 페이지 DOM + A/B가 확정한 scenario 계약 의존 |
| 4 | E | D가 만든 결과 컨테이너 의존 |

## Success Criteria mapping (CONTEXT.md 기준 1-7)

| # | 기준 | 담당 항목 | 검증 방법 |
|---|------|-----------|-----------|
| 1 | 미로그인: 프로파일 열람 가능, 생성 시 로그인 유도 | C-2(클라이언트 게이트) + A-2(서버 401 강제) | Verification C 2·3번, Verification A 1번 |
| 2 | 로그인: 양방향 모두 실제 LLM 응답 수신 | B-1/B-2 + C-2(양 탭) | Verification B 1번 + C 4번 실측 |
| 3 | 빈응답/429 시 폴백 모델 자동 전환 | B-1(MODEL_CHAIN + 오류 분류) | Verification B 2번(model_used=deepseek-chat 실측) |
| 4 | 결과가 F1~F9 전부 포함, 누락 시 재생성·폴백 작동 | B-1(validateScenario + 재생성 1회→회전 흐름) | Verification B 1·3번(게이트 재검증) + B 2번(회전) |
| 5 | MKT-05 대로 카드+타임라인+검색창 목업 렌더링 | D(전체) | Verification D 스크린샷 실측 |
| 6 | 일일 상한 초과 차단 | A-2(D1 reserve 카운터) | Verification A 3번(6회차 429 실측) |
| 7 | 빌드 0에러, AdSense ID 계열 위반 없음 | 전 항목 빌드 게이트 + E | 각 Verification `npm run build` + E grep(타 계열 pub ID 0건) |

## 사용자 설정 (에이전트 불가 작업)

- Cloudflare Pages Secrets `NVIDIA_API_KEY`, `DEEPSEEK_API_TOKEN` — B-3 스크립트로 자동 등록 시도, wrangler 인증 실패 시에만 대시보드 수동 등록 요청(기존 `.env`/`~/.env.common` 값 재사용)

## 범위 밖 (명시적 — A-1..A-5 초과 안 함)

- 결과 D1 저장(A-4: 후속), N회 무료체험 게이트(MKT-01 대안 — 현재 결정은 로그인 필수), 내비/Sitemap 링크 추가, decision-cards.json 프롬프트 주입(재료는 personaKey 통계 요약으로 충분), 서버 이미지 생성(MKT-05가 CSS 렌더만 명시)
