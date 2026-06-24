# scheduler.py
"""
auto-writer 스케줄러.
launchd 또는 직접 실행으로 pipeline.py를 호출한다.

사용법:
  python3 scheduler.py              # 즉시 실행 (발행)
  python3 scheduler.py --dry-run    # 데이터 확인만, 발행 안 함
  python3 scheduler.py --status     # 오늘 발행 현황만 출력
  python3 scheduler.py --fetch      # 데이터 수집만 (발행 없음)
"""
import os, sys, logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv("/Users/twinssn/Projects/money-aikorea24/.env")
load_dotenv(os.path.expanduser("~/.env.common"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR  = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "scheduler.log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scheduler")

def print_status():
    """오늘 발행 현황 출력"""
    sys.path.insert(0, BASE_DIR)
    from shared.db_utils import get_conn, get_today_published_count, get_pending_count

    today        = datetime.now().strftime("%Y-%m-%d")
    today_count  = get_today_published_count()
    pending      = get_pending_count()
    daily_quota  = int(os.getenv("DAILY_QUOTA", "5"))

    conn = get_conn()
    recent = conn.execute(
        """SELECT title, category, persona, published_at, model_used
           FROM publish_ledger
           WHERE published_at LIKE ?
           ORDER BY published_at DESC""",
        (f"{today}%",)
    ).fetchall()
    conn.close()

    print(f"\n{'='*55}")
    print(f" auto-writer 현황 — {today}")
    print(f"{'='*55}")
    print(f" 오늘 발행: {today_count}/{daily_quota}건")
    print(f" 대기 중:   {pending:,}건")
    print(f"{'─'*55}")
    if recent:
        for r in recent:
            model_short = (r["model_used"] or "").split("/")[-1][:20]
            print(f" [{r['category']:<10}] {r['title'][:28]}")
            print(f"           모델: {model_short} | {r['published_at'][11:16]}")
    else:
        print(" 오늘 발행된 글 없음")
    print(f"{'='*55}\n")

def run_fetch():
    """데이터 수집만 실행 (발행 없음)"""
    logger.info("데이터 수집 시작 (--fetch)")

    try:
        sys.path.insert(0, BASE_DIR)
        from fetcher          import fetch_all as fetch_gov24
        from fetcher_loan_fin import fetch_all as fetch_finlife
        from fetcher_invest    import fetch_all as fetch_invest

        fetch_gov24()
        fetch_finlife()
        fetch_invest()
        logger.info("데이터 수집 완료")

    except Exception as e:
        logger.error(f"데이터 수집 오류: {e}", exc_info=True)

        from shared.notifier import send
        send(f"데이터 수집 크래시\n`{str(e)[:200]}`", "ERROR")
        sys.exit(1)

def run(dry_run=False):
    logger.info(f"{'[DRY-RUN] ' if dry_run else ''}스케줄러 시작")

    try:
        sys.path.insert(0, BASE_DIR)
        from pipeline import run as pipeline_run
        pipeline_run(dry_run=dry_run)
        logger.info("스케줄러 정상 종료")

    except Exception as e:
        logger.error(f"스케줄러 오류: {e}", exc_info=True)

        from shared.notifier import send
        send(f"스케줄러 크래시\n`{str(e)[:200]}`", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    if "--status" in sys.argv:
        print_status()
    elif "--dry-run" in sys.argv:
        run(dry_run=True)
    elif "--fetch" in sys.argv:
        run_fetch()
    else:
        run(dry_run=False)
