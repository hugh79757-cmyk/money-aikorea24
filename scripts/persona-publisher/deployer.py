"""
Persona Publisher — Deployer
astro build + wrangler deploy + post-build validation + Telegram 알림
"""
import os
import re
import subprocess
import sys

PROJECT_DIR = "/Users/twinssn/projects/money-aikorea24"

# .env 의 TELEGRAM_BOT_TOKEN 사용 (deployer.py는 publisher.py를 통해 호출되므로)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def send_telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[telegram] 미설정 — 메시지 스킵: {msg}")
        return
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
        print("[telegram] 알림 전송 완료")
    except Exception as e:
        print(f"[telegram] 전송 실패: {e}")


def _parse_collection_errors(stderr: str) -> list[dict]:
    """
    빌드 stderr에서 콘텐츠 컬렉션 스키마 오류를 파싱.
    반환: [{file, error, line}] 형태의 리스트
    """
    errors = []

    # Astro 에러 패턴 예시:
    #   error   src/content/blog/foo.md:1:1: Invalid frontmarkdown...
    #   error   [zod] Expected array, received string at "tags"
    lines = stderr.split("\n")
    current_file = None
    current_error = None

    for line in lines:
        # 파일 경로가 포함된 에러 라인 감지
        file_match = re.search(
            r'(?:src/content/(?:blog|nomad)/[^:\s]+\.md)', line
        )
        if file_match:
            current_file = file_match.group(0)

        # Zod validation 에러 감지
        zod_match = re.search(
            r'Expected\s+(.+?),\s*received\s+(.+?)(?:\s+at\s+\"(\w+)\")?', line,
            re.IGNORECASE
        )
        if zod_match and current_file:
            expected = zod_match.group(1)
            received = zod_match.group(2)
            field = zod_match.group(3) or "unknown"
            err = {
                "file": current_file,
                "field": field,
                "expected": expected,
                "received": received,
                "detail": line.strip(),
            }
            if err not in errors:
                errors.append(err)
            continue

        # "Invalid frontmatter" 패턴
        if "invalid frontmatter" in line.lower() and current_file:
            err = {
                "file": current_file,
                "field": "frontmatter",
                "expected": "valid frontmatter",
                "received": "invalid",
                "detail": line.strip(),
            }
            if err not in errors:
                errors.append(err)

    return errors


def _auto_fix_file(filepath: str) -> list[str]:
    """
    단일 파일에 validator를 적용하여 frontmatter 오류 수정.
    반환: 적용된 fix 설명 목록
    """
    try:
        # validator 모듈을 publisher와 동일한 방식으로 import
        sys.path.insert(0, os.path.join(PROJECT_DIR, "scripts", "persona-publisher"))
        import validator
        import transformer

        # 폴백: transformer도 같은 경로에서
        if "transformer" not in sys.modules:
            import importlib
            transformer = importlib.import_module("transformer")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        fixed_content, fixes = validator.validate_and_fix_content(content)

        # 내용 정규화 (heroImage 경로 등)
        fname = os.path.basename(filepath)
        normalized_fname, fixed_content, name_fixes = validator.normalize_file_content(
            fname, fixed_content
        )
        fixes.extend(name_fixes)

        if fixes:
            # 파일명이 변경된 경우
            if normalized_fname != fname:
                new_path = os.path.join(os.path.dirname(filepath), normalized_fname)
                os.rename(filepath, new_path)
                with open(new_path, "w", encoding="utf-8") as f:
                    f.write(fixed_content)
                print(f"[auto-fix] 파일명 변경: {fname} → {normalized_fname}")
                print(f"[auto-fix] {new_path} 수정 완료 ({len(fixes)}건)")
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(fixed_content)
                print(f"[auto-fix] {filepath} 수정 완료 ({len(fixes)}건)")

            for f in fixes:
                print(f"  - {f}")

        return fixes
    except Exception as e:
        print(f"[auto-fix] 파일 처리 실패 {filepath}: {e}")
        return []


def build_and_deploy(count: int) -> bool:
    """
    astro build + wrangler deploy
    count: 새로 추가된 파일 수
    반환: 성공 여부

    빌드 실패 시:
      1. stderr에서 콘텐츠 컬렉션 에러 파싱
      2. 해당 파일 auto-fix
      3. 1회 재시도
      4. 재시도도 실패하면 Telegram 알림
    """
    print(f"[deployer] 빌드 시작 ({count}개 신규 파일)")

    # ---- 1차 빌드 시도 ----
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("[deployer] 빌드 성공, 배포 시작")
        return _deploy(count)

    # ---- 빌드 실패 — 에러 분석 + auto-fix ----
    combined = result.stderr + "\n" + result.stdout
    print("[deployer] 빌드 실패 — 에러 분석 중...")

    # 에러 로그 출력 (처음 1000자)
    print(f"[deployer] stderr (처음 1000자):\n{result.stderr[:1000]}")

    errors = _parse_collection_errors(combined)
    if not errors:
        # 파싱할 수 없는 에러 → 수동 발행 요청
        msg = (
            f"🚨 자동 발행 실패 — 수동 발행 필요\n"
            f"원인: 알 수 없는 빌드 에러\n"
            f"실행 명령: python3 scripts/persona-publisher/publisher.py\n"
            f"stderr: {result.stderr[-300:]}"
        )
        send_telegram(msg)
        return False

    # 에러 메시지 구성
    error_summary = "\n".join(
        f"  - {e['file']}: {e['field']} (expected {e['expected']}, got {e['received']})"
        for e in errors[:5]
    )
    print(f"[deployer] 콘텐츠 컬렉션 에러 ({len(errors)}건):\n{error_summary}")

    # 에러 발생 파일들에 대해 auto-fix 시도
    fixed_any = False
    for err in errors:
        filepath = os.path.join(PROJECT_DIR, err["file"])
        if os.path.exists(filepath):
            fixes = _auto_fix_file(filepath)
            if fixes:
                fixed_any = True

    if not fixed_any:
        msg = (
            f"🚨 자동 발행 실패 — 수동 발행 필요\n"
            f"원인: auto-fix 불가 (스키마 오류)\n"
            f"에러 ({len(errors)}건):\n{error_summary}\n"
            f"\n수동 실행: python3 scripts/persona-publisher/publisher.py"
        )
        send_telegram(msg)
        return False

    # ---- 2차 재빌드 시도 ----
    print("[deployer] auto-fix 완료, 재빌드 시도...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("[deployer] auto-fix 후 재빌드 성공, 배포 시작")
        return _deploy(count)

    # ---- 2차도 실패 — Telegram 수동 발행 요청 ----
    msg = (
        f"🚨 자동 발행 실패 — 수동 발행 필요\n"
        f"원인: auto-fix 후에도 빌드 실패\n"
        f"1차 에러:\n{error_summary}\n"
        f"\n수동 실행: python3 scripts/persona-publisher/publisher.py"
    )
    send_telegram(msg)
    return False


def _deploy(count: int) -> bool:
    """wrangler pages deploy"""
    # money-aikorea24/.env의 CLOUDFLARE 토큰 주입 (oauth_token 만료 대응)
    from dotenv import load_dotenv as _ldenv
    _ldenv(os.path.join(PROJECT_DIR, ".env"), override=True)
    _deploy_env = os.environ.copy()
    _cf_token = os.getenv("CLOUDFLARE_API_TOKEN", "")
    _cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    if _cf_token:
        _deploy_env["CLOUDFLARE_API_TOKEN"] = _cf_token
    if _cf_account:
        _deploy_env["CLOUDFLARE_ACCOUNT_ID"] = _cf_account
    result = subprocess.run(
        ["npx", "wrangler", "pages", "deploy", "dist/",
         "--project-name", "money-aikorea24",
         "--commit-dirty=true",
         "--commit-message=feat: auto publish new posts"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        env=_deploy_env,
    )
    if result.returncode != 0:
        msg = (
            f"🚨 자동 발행 실패 — 수동 발행 필요\n"
            f"원인: Cloudflare Pages 배포 실패\n"
            f"stderr: {result.stderr[-300:]}\n"
            f"수동 실행: python3 scripts/persona-publisher/publisher.py"
        )
        print(msg)
        send_telegram(msg)
        return False

    msg = f"✅ 배포 완료: 새 글 {count}개 발행됨"
    print(f"[deployer] {msg}")
    return True
