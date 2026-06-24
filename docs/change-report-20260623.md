# 변경 리포트 — 2026-06-23

## 1. 모델 폴백 체인 교체 (committed: `f3fcfd9`)

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 메인 모델 | deepseek-v4-flash, diffusiongemma-26b | **diffusiongemma-26b** (retry 2) |
| 1차 폴백 | deepseek-v4-flash | gemma-4-31b-it |
| 2차 폴백 | deepseek-v4-pro | gemma-3n-e4b-it |
| deepseek 계열 | 3개 모두 사용 | **전면 제거** (429 지속) |

**writer.py**: `stream=True`, `max_tokens=8192`, `temperature=0.6`, `top_p=0.9`, `frequency_penalty=0.3`, `presence_penalty=0.3`, `max_retries` 미설정(SDK 기본 2).

## 2. SYSTEM_PROMPT 전면 재설계 (committed: `a94b2c1`)

- **이모지 전면 금지** — "친한 선배가 알려주는 대화체" → 객관적 정보 전달체
- `[RELATED_POSTS]`/`[PERSONA_CTA]`는 H2 제목 내 포함 금지 규칙 추가
- DAILY_QUOTA 기본값 999 (테스트 기간 제한 해제)

## 3. 퍼널 링크 3개 버그 수정 (committed: `5c02e5b`, `f3fcfd9`)

### 3a. reviewer.py 마커 복원 버그 (`5c02e5b`)
- `_restore_markers(protected_body, marker_map)` 호출로 수정
- 기존: `_restore_markers(body, {v: k for k, v in marker_map.items()})` — `[RELATED_POSTS]`가 `**MARKER_RELATED_POSTS_0**`(볼드)로 깨짐

### 3b. PERSONA_CTA 블록 함수 추가 (`5c02e5b`)
- `make_persona_cta_block(cta_url, persona)` — 7종 문구 분기 (`PERSONA_CTA_TEXTS`)
- `remove_fake_links()` — example.com/example.org/#/javascript: 패턴 제거
- `clean_prompt_leaks()` — H2 내 SYSTEM_PROMPT 지시문 누출 제거
- CTA 블록/SUMMARY_BOX 이모지 제거
- 인라인 CTA 문구: "예상 금액 계산" → **"내 페르소나 통계 보기"** (my-persona 기능 일치)

### 3c. reviewer → validator 순서 버그 (uncommitted, `pipeline.py`)
- **증상**: `validate_and_fix`가 `[PERSONA_CTA]`를 CTA 블록으로 교체 → `review_article`의 `_ensure_markers`가 `[PERSONA_CTA]`가 없다고 판단해 **새로 삽입** → 발행글에 `[PERSONA_CTA]` raw 텍스트 노출
- **수정**: reviewer(마커 보호/복원) → validator(CTA 교체) 순서로 변경
- **결과**: 4건 재발행 검증 — raw marker 0, CTA 블록 정상

## 4. CTA 추적 파라미터 전면 도입 (uncommitted)

모든 my-persona 링크에 `?src=` 추적 파라미터 추가:

| 위치 | src 형식 | 예시 |
|------|----------|------|
| category_map.yaml (메인 CTA) | `?src=cta-{persona}` | `cta-youth`, `cta-worker` |
| pipeline.py (인라인 CTA) | `?src=inline-{type}-{cat}-{persona}` | `inline-peer-loan-lowincome` |
| BlogPost.astro entity-card | `?src=blog-card-{cat}` | `blog-card-loan` |

`validator.py` orphan URL regex도 `?src=` variant까지 커버하도록 확장.

## 5. 카드 이미지 URL 전환 (uncommitted)

`/cards/{key}.jpg` → `https://cards.persona.aikorea24.kr/{key}.jpg` (CDN 도메인 직접 참조)

적용 파일:
- `src/pages/index.astro` (Hero 배경)
- `src/pages/my-persona.astro` (Hero 배경, 카드 미리보기, Canvas 생성, 공유 이미지)
- `src/pages/persona/[...slug].astro` (OG 이미지, 카드 표시, 모바일 카드)

## 6. 기타 수정 (uncommitted)

- `BlogPost.astro`: 테이블 th/td에 다크모드 CSS 변수 적용 (`--color-border-light`, `--color-code-bg`)
- `login.astro`: KAKAO_REST_KEY 하드코딩 폴백 제거, **env var 필수**로 변경
- `design-tokens.css`: `--color-info` 변수 추가

## 7. 발행글 전량 삭제 (uncommitted)

- `src/content/blog/` — **267개 .md 파일 전량 삭제** (자동발행글 + TODO 템플릿)
- `publish_ledger` 16건 삭제
- `services` 16건 → `pending` 복원
- 현재: `pending 5,476`, `error 1`
