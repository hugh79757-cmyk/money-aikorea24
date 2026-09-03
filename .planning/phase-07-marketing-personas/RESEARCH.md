# Research: Phase 7 Marketing Persona Studio

> 출처: 2026-08-23 세션 실측 (파일 직접 읽기, 브라우저 라이브 확인, API 호출). 추론 표시 별도.

## 1. 데이터 자산 (마케팅 페르소나 원재료)

| 자산 | 규모 | 내용 | 활용 가능성 |
|---|---|---|---|
| `public/persona-stats.json` | 2,244키 (지역_성별_연령1년단위), 25MiB | education/family/housing/income/jobs/marital/personas/total 필드. 지역명 짧은 형식(경남·충북 등) | 인구통계+소득+직업 = 페르소나 프로파일 코어. **배포 시 제외됨**(25MiB 제한) |
| `public/persona-stats-decade.json` | 204키(10년 단위), 4MiB | 위의 서브셋 | my-persona.astro가 런타임 fetch하는 선례 — 신규 페이지도 이 패턴 재사용 가능 |
| `src/data/decision-cards.json` | 204키(10년 단위) | personaKey/totalMatchedCount/topThree(welfare_name·eligibility_summary)/totalEligibleAnnual | "이 페르소나가 받는 지원금" → 고민·니즈 추정 재료 |
| `public/benefits-clean.json` + `src/lib/benefitMatcher.ts` | 수천 건 | 점수 기반 매칭(data-age-range/data-regions) | product-first: 제품 타깃 조건→유사 조건 페르소나 역매칭에 matcher 로직 참조 |
| `src/data/wage-table.json`, `job-category-map.json` | 직종별 | 임금+보정계수, 직업→10카테고리 매핑 | 소비력 추정 |

**검증 방법**: python3 json.load로 구조 직접 출력 (세션 m0109).

## 2. 기존 흐름·인프라 (재사용 후보)

- **my-persona.astro**: 다단계 입력 SPA → 결과. 마케팅 페르소나 UI의 구조적 선례. `persona-stats-decade.json` 런타임 fetch.
- **persona/[...slug].astro**: getStaticPaths 2,244개 SSG. URL `/persona/{지역}-{성별}-{연령}/`. benefits 딥링크(`/benefits?age=&region=`) 이미 구현·배포됨 (`benefits/index.astro:442-524`, caller `[...slug].astro:649` — 세션 브라우저 실측).
- **인증**: 카카오 OAuth + HMAC-SHA256 세션. 쿠키 2종(HttpOnly `session` / UI용 `session_ui`). Pages Secrets 필수 3개(KAKAO_REST_KEY/KAKAO_CLIENT_SECRET/SESSION_SECRET). → "가벼운 게이트"를 기존 로그인으로 충족 가능.
- **동적 API 선례**: `functions/api/**` Cloudflare Pages Functions + D1(`persona-db`) — 커뮤니티 CRUD, 좋아요 집계 등. LLM 프록시 엔드포인트를 여기에 추가하는 패턴이 자연스러움.
- **LLM 폴백 체인**: `scripts/auto-writer/writer.py` — 5 프로바이더(nvidia/deepseek/google/groq/cerebras) 11모델, persistent rotation state(db/fallback_state.json), quota 5분/structural 1시간 cooldown, trace 로깅. **Python·로컬 실행** — 런타임 웹 사용엔 JS 포팅 필요. OpenRouter 키는 2026-08-23 신규 발급(~/.env.common:140)하나 이 repo 코드는 미사용.

## 3. 제약 조건 (실측)

1. `output: 'static'` — frontmatter 로직은 빌드타임만 실행. 실시간 LLM은 반드시 Functions 경유.
2. Cloudflare 파일 25MiB 제한 — 생성물 JSON도 용량 주의.
3. AdSense 계열: aikorea24 전용 `ca-pub-5938862195544185` (글로벌 AGENTS.md 매핑표). 광고 슬롯 넣을 경우 이 ID만.
4. 무료 LLM 공유풀 특성(세션 실측): llama-3.3-70b:free=404(deprecated), z-ai/glm-5.2:free=upstream 429, lfm-2.5=빈 reasoning-only 응답, nemotron-3.5-lightning:free=200 정상. → 폴백 체인 없이 단일 모델 의존은 위험.
5. `.env`(프로젝트) → `~/.env.common`(전역) 폴백. 런타임 시크릿은 Cloudflare Pages Secrets만 유효(.env 무시).

## 4. 리스크 메모

- 실시간 LLM 비공개 호출 = 남용 리스크 → 게이트(로그인) + 사용량 상한 필요. D1에 일일 카운터 패턴 선례(benefit-click 집계) 있음.
- LLM 출력 품질: writer.py의 품질 게이트(마커 검증+최소 길이)+validator 패턴을 JS 쪽에도 최소한으로 이식 권장 (프롬프트 릭/빈 응답 방지 — llm-fallback-chain-management 스킬 준거).
- 개인정보: 페르소나는 통계 기반 가상 인물이므로 실명·실존 데이터 아님. 다만 "특정인 연상" 방지 문구 권장.

## 5. 미해결 질문 (플래너가 가정으로 처리)

- 진입점 URL 명칭 (/marketing-persona 가정)
- 게이트 강도 (로그인 필수 vs N회 무료체험 후 로그인 — CONTEXT 가정参照)
- 결과 저장 여부 (D1 저장 vs 세션 상태만)
