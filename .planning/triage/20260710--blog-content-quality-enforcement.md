---
date: 2026-07-10
type: chore
status: resolved
---

# Blog 콘텐츠 품질 전수조사 및 재발방지 체계 구축

## What
전체 블로그 글(200개)에 대해 콘텐츠 품질 이슈 전수조사 + 일괄 수정 + 재발방지 자동화

## Why
BlogPost.astro에 내장 TOC가 있음에도 auto-writer 파이프라인에서 `**목차**` 수동 TOC를 생성하여 본문에 삽입 — 194개 글에서 중복 렌더링 발생. 또한 LLM 출력에서 `<|channel>thought` 등의 AI 아티팩트 누출 가능성 존재.

## Files changed
- `scripts/auto-writer/pipeline.py` — build_summary_box() 호출 비활성화
- `scripts/auto-writer/validator.py` — remove_ai_artifacts() 추가, validate_and_fix()에 통합
- `scripts/check-blog-issues.py` — 신규 생성: pre-build validation scanner
- `scripts/auto-writer/shared/build_deploy.py` — 배포 전 check 스크립트 통합
- `scripts/deploy.sh` — 배포 전 check 스크립트 통합 (1/5 단계), 단계 번호 보정
- `src/content/blog/*.md` — 194개 파일 **목차** 제거, 1개 파일 중복 H1 수정

## How
1. **전수조사**: 7개 체크리스트로 200개 파일 스캔 — 194건 **목차**, 1건 중복 H1 발견
2. **일괄 수정**: bash/python 스크립트로 TOC 섹션 제거, 중복 H1 → H2 변환
3. **재발방지 3단계**:
   - Root cause: pipeline.py build_summary_box() 비활성화
   - Safety net: validator.py remove_ai_artifacts() (파이프라인 validate 단계에서 자동 정화)
   - Pre-build gate: scripts/check-blog-issues.py (deploy.sh + build_deploy.py에서 --ci 모드로 실행, 문제 시 배포 중단)

## Verification
- `python3 scripts/check-blog-issues.py` — "All 200 blog posts clean — no issues found." 확인
