# Phase 8: Auto-writer GitHub Actions Migration

## Goal
MacBook 꺼져도 auto-writer가 자동 발행되도록 GitHub Actions로 마이그레이션.
최소 트리거 패턴: Actions가 콘텐츠 생성+commit만 하고, Cloudflare Pages가 자동 build+deploy 담당.

## Architecture

```
GitHub Actions (매일 09:00 UTC = 18:00 KST)
  ├─ 1. git pull (SQLite DB 포함)
  ├─ 2. python3 scripts/auto-writer/ci_generate.py
  │     ├─ check-blog-issues.py --fix (선행 수정)
  │     ├─ pipeline.py run() (LLM → .md → thumbnail → R2 업로드)
  │     └─ SQLite DB 업데이트
  ├─ 3. git add -A && git commit && git push
  └─ 4. (끝)

Cloudflare Pages (자동 감지)
  └─ git push 감지 → Astro build → 배포
```

## Tasks

### T1: check-blog-issues.py LEADING_SPACE 버그 수정
**Files**: `scripts/check-blog-issues.py`
**Problem**: 
- `scan_file()` line 76: `if line != s` — trailing whitespace도 LEADING_SPACE로 감지
- `fix_issues()` line 184: LEADING_SPACE를 remaining에서 필터링 → "clean" 보고但实際은 문제 지속
**Fix**:
1. line 76: `if line != s` → `if line.lstrip() != s` (leading만 체크)
2. line 184: LEADING_SPACE 필터 제거 또는 fix 로직에 rstrip() 추가
3. 테스트: `--ci` 모드에서 exit 0 확인

### T2: build_deploy.py 분리
**Files**: `scripts/auto-writer/shared/build_deploy.py`
**Change**: 
- 기존 `run()` 유지 (로컬용)
- 새 `generate_only()` 함수: build/deploy 없이 콘텐츠 생성+commit만
- 또는 별도 `ci_generate.py` 스크립트 생성

### T3: ci_generate.py 생성
**Files**: `scripts/auto-writer/ci_generate.py` (신규)
**Logic**:
```python
# 1. check-blog-issues.py --fix 실행
# 2. pipeline.py run() (기존 파이프라인)
# 3. build_deploy.py의 build/deploy 스킵
# 4. git add -A && git commit && git push
```
**Key**: `build_deploy.py`의 `run()`을 호출하지 않고, 파이프라인 생성 부분만 실행

### T4: .github/workflows/auto-writer.yml 작성
**Files**: `.github/workflows/auto-writer.yml` (신규)
**Config**:
```yaml
on:
  schedule:
    - cron: '0 9 * * *'  # 09:00 UTC = 18:00 KST
  workflow_dispatch:       # 수동 트리거

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - run: python3 scripts/auto-writer/ci_generate.py
        env:
          NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY }}
          DEEPSEEK_API_TOKEN: ${{ secrets.DEEPSEEK_API_TOKEN }}
          MIMO_API_KEY: ${{ secrets.MIMO_API_KEY }}
          DATA_GO_KR_API_KEY: ${{ secrets.DATA_GO_KR_API_KEY }}
          FINLIFE_API_KEY: ${{ secrets.FINLIFE_API_KEY }}
          CF_R2_ACCESS_KEY_ID: ${{ secrets.CF_R2_ACCESS_KEY_ID }}
          CF_R2_SECRET_ACCESS_KEY: ${{ secrets.CF_R2_SECRET_ACCESS_KEY }}
```

### T5: GitHub Secrets 세팅
**Action**: GitHub repo Settings → Secrets → Actions에 아래 secrets 추가:
- `NVIDIA_API_KEY`
- `DEEPSEEK_API_TOKEN`
- `MIMO_API_KEY`
- `DATA_GO_KR_API_KEY`
- `FINLIFE_API_KEY`
- `CF_R2_ACCESS_KEY_ID`
- `CF_R2_SECRET_ACCESS_KEY`
- `NAVER_CLIENT_ID` (topic_relevance용)
- `NAVER_CLIENT_SECRET`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### T6: persona-stats.json 처리
**Finding**: 25MiB 파일이 git 추적 중 — Actions clone 30-60초 추가
**Decision**: 현상 유지 (추적 유지). daily workflow에선 허용 범위.
**Optional future**: Git LFS 전환으로 clone 속도 개선

### T7: 로컬 launchd와 공존
**Current**: launchd가 매일 09:00 KST에 scheduler.py 실행
**Change**: 
- GitHub Actions가 09:00 UTC (18:00 KST)에 실행
- 로컬 launchd는 비활성화 또는 충돌 방지
- **권고**: launchd 비활성화 (`launchctl unload`)

## Acceptance Criteria

- [ ] `check-blog-issues.py --ci` → exit 0 (LEADING_SPACE 수정)
- [ ] `ci_generate.py` 실행 → .md 생성 + DB 업데이트 + git commit
- [ ] GitHub Actions 첫 실행 성공 (워크플로우 완료)
- [ ] Cloudflare Pages 자동 배포 확인
- [ ] MacBook 꺼진 상태에서 24시간 후 발행 확인

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| persona-stats.json clone 느림 | 워크플로우 +30-60s | 현상 유지, 허용 범위 |
| GitHub Actions 무료 한도 초과 | 월 2000분 | 1일1회 = 300분/월, 여유 |
| SQLite DB git 충돌 | 드무나 복잡 | Actions가 유일한 편집자 |
| check-blog-issues.py 미수정 | build/deploy 차단 | T1 선행 |

## Time Estimate

| Task | Time |
|------|------|
| T1: LEADING_SPACE 수정 | 10-15분 |
| T2: build_deploy 분리 | 10-15분 |
| T3: ci_generate.py | 15-20분 |
| T4: GitHub Actions YAML | 10-15분 |
| T5: Secrets 세팅 | 5-10분 |
| T6-7: 검증 | 10-15분 |
| **합계** | **60-90분** |
