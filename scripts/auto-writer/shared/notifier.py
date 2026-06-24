"""
Telegram 알림 정책:
  - ERROR : 즉시 발송 (빌드 실패, 모든 모델 실패, DB 오류)
  - WARN  : 즉시 발송 (GPT 재시도 초과, 검수 실패, R2 업로드 실패)
  - INFO  : 발송 안 함 (성공, 발행 완료 등 — 로컬 로그만 기록)
"""
import os, requests, logging
from dotenv import load_dotenv

load_dotenv("/Users/twinssn/Projects/money-aikorea24/.env")
load_dotenv(os.path.expanduser("~/.env.common"))

TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# INFO는 전송하지 않음
NOTIFY_LEVELS = {"WARN", "ERROR"}

logger = logging.getLogger("notifier")

def send(message: str, level: str = "INFO"):
    """
    level="ERROR" 또는 "WARN"일 때만 Telegram 발송.
    level="INFO"는 로컬 로그만 기록하고 무시.
    """
    emoji = {"INFO": "✅", "WARN": "⚠️", "ERROR": "🚨"}.get(level, "ℹ️")

    # 로컬 로그는 항상 기록
    log_msg = f"[{level}] {message}"
    if level == "ERROR":
        logger.error(log_msg)
    elif level == "WARN":
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

    # INFO는 Telegram 발송 안 함
    if level not in NOTIFY_LEVELS:
        return

    if not TOKEN or not CHAT_ID:
        logger.warning(f"Telegram 키 없음 (발송 실패): {message}")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id":    CHAT_ID,
                "text":       f"{emoji} [auto-writer]\n{message}",
                "parse_mode": "Markdown"
            },
            timeout=10
        )
    except Exception as e:
        logger.warning(f"Telegram 전송 실패: {e}")
