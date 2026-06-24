import os, subprocess
from dotenv import load_dotenv

load_dotenv("/Users/twinssn/Projects/money-aikorea24/.env")
load_dotenv(os.path.expanduser("~/.env.common"))

PROJECT_DIR = "/Users/twinssn/Projects/money-aikorea24"

def run(count: int = 0) -> bool:
    env = os.environ.copy()
    try:
        print("[deploy] Astro 빌드 시작...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=PROJECT_DIR, env=env,
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            print(f"[deploy] 빌드 실패:\n{result.stderr[-500:]}")
            return False

        print("[deploy] Wrangler 배포 시작...")
        result = subprocess.run(
            ["npx", "wrangler", "pages", "deploy", "dist/",
             "--project-name", "money-aikorea24",
             "--commit-dirty=true"],
            cwd=PROJECT_DIR, env=env,
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            print(f"[deploy] 배포 실패:\n{result.stderr[-500:]}")
            return False

        print(f"[deploy] 배포 완료 ({count}건 발행)")
        return True

    except subprocess.TimeoutExpired:
        print("[deploy] 타임아웃")
        return False
