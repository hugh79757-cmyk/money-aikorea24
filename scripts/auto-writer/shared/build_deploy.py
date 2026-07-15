import os, sys, subprocess
from dotenv import load_dotenv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import paths

load_dotenv(paths.DOTENV_PATH)
load_dotenv(paths.COMMON_ENV_PATH)

PROJECT_DIR = paths.PROJECT_ROOT

def run(count: int = 0) -> tuple[bool, str]:
    """Returns (success: bool, detail: str) where detail explains the failure."""
    env = os.environ.copy()
    # wrangler 4.x: CLOUDFLARE_API_TOKEN env var overrides OAuth auth profile.
    # Remove it so wrangler uses the bound profile (hugh79757).
    env.pop("CLOUDFLARE_API_TOKEN", None)
    try:
        print("[deploy] 블로그 글 사전 검증...")
        check_result = subprocess.run(
            [sys.executable, "scripts/check-blog-issues.py", "--ci"],
            cwd=PROJECT_DIR, capture_output=True, text=True, timeout=60
        )
        if check_result.returncode != 0:
            detail = check_result.stdout or check_result.stderr
            print(f"[deploy] 블로그 글 검증 실패:\n{detail}")
            return (False, f"CHECK_FAILED:{detail[:300]}")
        print("[deploy] 모든 블로그 글 정상. Astro 빌드 시작...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=PROJECT_DIR, env=env,
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            detail = _extract_error_detail(result, "build")
            print(f"[deploy] 빌드 실패:\n{detail}")
            return (False, detail)

        print("[deploy] dist/persona-stats.json 제거 (25MiB 파일 제한)")
        os.remove(os.path.join(PROJECT_DIR, "dist", "persona-stats.json"))

        # Use /opt/homebrew/bin/wrangler (not npx/cached 4.92.0) for auth profile support
        WRANGLER = "/opt/homebrew/bin/wrangler"
        print("[deploy] Wrangler 배포 시작...")
        result = subprocess.run(
            [WRANGLER, "pages", "deploy", "dist/",
             "--project-name", "money-aikorea24",
             "--commit-dirty=true"],
            cwd=PROJECT_DIR, env=env,
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            detail = _extract_error_detail(result, "wrangler")
            print(f"[deploy] 배포 실패:\n{detail}")
            return (False, detail)

        print(f"[deploy] 배포 완료 ({count}건 발행)")
        return (True, "")

    except subprocess.TimeoutExpired:
        msg = "npm build 또는 wrangler deploy 300초 타임아웃"
        print(f"[deploy] {msg}")
        return (False, msg)


def _extract_error_detail(result: subprocess.CompletedProcess, phase: str) -> str:
    """Pick the most informative snippet from stderr/stdout for Telegram."""
    stderr = (result.stderr or "").strip()
    stdout = (result.stdout or "").strip()

    if phase == "build":
        # Astro build errors: look for the first [cause] or error line
        lines = (stderr + "\n" + stdout).splitlines()
        # Collect lines containing common error markers
        picks = [l.strip() for l in lines
                 if any(kw in l.lower() for kw in
                        ["error", "cause", "failed", "build failed",
                         "cannot find", "module not found",
                         "syntax error", "referenceerror", "typeerror"])]
        if not picks:
            picks = lines[-5:]  # last 5 lines as fallback
        return "\n".join(picks[-8:])  # at most 8 lines
    else:
        # Wrangler deploy: return last 500 chars of stderr
        return stderr[-500:]
