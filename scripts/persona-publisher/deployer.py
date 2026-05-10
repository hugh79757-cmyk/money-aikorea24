import os
import subprocess
import requests

PROJECT_DIR = "/Users/twinssn/projects/money-aikorea24"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def send_telegram(msg: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[telegram] 미설정 — 메시지 스킵: {msg}")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print(f"[telegram] 전송 실패: {e}")


def build_and_deploy(count: int) -> bool:
    """
    astro build + wrangler deploy
    count: 새로 추가된 파일 수
    반환: 성공 여부
    """
    print(f"[deployer] 빌드 시작 ({count}개 신규 파일)")

    # npm run build
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        msg = f"❌ persona-publisher 빌드 실패\n{result.stderr[-500:]}"
        print(msg)
        send_telegram(msg)
        return False

    print("[deployer] 빌드 성공, 배포 시작")

    # wrangler pages deploy
    result = subprocess.run(
        ["npx", "wrangler", "pages", "deploy", "dist/",
         "--project-name", "money-aikorea24"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        msg = f"❌ persona-publisher 배포 실패\n{result.stderr[-500:]}"
        print(msg)
        send_telegram(msg)
        return False

    msg = f"✅ persona.aikorea24.kr 배포 완료\n새 글 {count}개 발행됨"
    print(f"[deployer] {msg}")
    send_telegram(msg)
    return True
