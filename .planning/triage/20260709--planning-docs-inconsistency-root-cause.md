---
date: 2026-07-09
type: docs
status: resolved
---

# .planning 중앙 문서 누락 + GSD skill 파일 분기로 인한 문서 불일치 원인 진단

## What
세션 시작 시 `.planning/` 디렉토리는 존재했으나 중앙 문서 5개(PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, config.json)가 없었고, GSD 엔진이 `project_exists=false`를 반환해 `/gsd-resume-work`·`/gsd-new-project` 등이 "프로젝트 미초기화"로 동작. phase 디렉토리(phase-02/03, 01-security-portability)와 PLAN/CONTEXT/SUMMARY는 존재해 "완료" 상태였으나 중앙 문서와 연결되지 않는 불일치 발생.

## Why
원인 2가지가 겹침:

1. **토대 scaffolding(`new-project`) 미커밋** — `.planning/`은 `5103da8`(codebase map)부터 추적됐지만, 중앙 문서 5개는 이번 세션 커밋 `f9db1f6` 이전엔 추적조차 되지 않음(= phase 작업만 개별 커밋되고 `new-project` 단계 산출물이 커밋되지 않음). GSD 엔진의 `detect-project.js`는 `config.json`/`PROJECT.md` 같은 프로젝트 마커 존재 여부로 `project_exists`를 판정하므로, 마커 부재 → `false` → "불일치"의 직접 원인.

2. **로드되는 skill과 canonical 설치의 파일 분기** — 실제 로드되는 `~/.config/opencode/get-shit-done/`이 canonical `~/.cline/gsd-core/` 대비 reference/template/workflow 파일 다수 누락(일부 0바이트). 이로 인해 `/gsd-new-project` 등 scaffolding 명령 자체가 실패 → 정상 커맨드로는 갭 복구 불가, 수동 복원 강제. (`003-rename-get-shit-done-to-gsd-core.cjs` 같은 마이그레이션이 있으나 미반영된 상태.)

## Files changed
- 백필(이번 세션 커밋 `f9db1f6`): `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/config.json`
- SUMMARY 생성(`f9db1f6`/`6071725`): `.planning/phase-02-content-freshness/SUMMARY.md`, `.planning/phase-03-adsense-optimization/SUMMARY.md`
- skill 파일 수동 복원(`.cline/gsd-core` → `~/.config/opencode/get-shit-done/`): `workflows/new-project.md`, `references/questioning.md`, `references/ui-brand.md`, `templates/project.md`, `templates/requirements.md`

## How
1. git 히스토리(`git log --oneline -- '.planning/'`, `git ls-files -- '.planning/'`)로 중앙 문서가 한 번도 커밋된 적 없음을 확인.
2. `detect-project` 출력(`project_exists=false; project_exists_robust=false`)과 `.planning/` 실존 상태 교차 검증 → 마커 파일 부재가 원인임을 확정.
3. 두 GSD 설치 디렉토리 파일 목록 비교로 skill 파일 분기 확인.
4. 부족한 중앙 문서를 코드 현실에 맞게 수동 백필 + SUMMARY 작성 + skill 누락 파일 복원 → 불일치 해소.

## Verification
- 백필 후 `git log --oneline -- '.planning/'`에 PROJECT/REQUIREMENTS/ROADMAP/STATE/config.json 추적 확인 (`f9db1f6`, `6071725`).
- 엔진 재실행 시 프로젝트 마커 존재로 `project_exists` 정상 판정 가능(backfilled).
- skill `new-project.md` 등 복원 후 `/gsd-*` 명령 로드 정상.
