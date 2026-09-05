import os, re, yaml, sys, logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from pathlib import Path

from title_generator import refinish_title

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import paths

load_dotenv(paths.DOTENV_PATH)
load_dotenv(paths.COMMON_ENV_PATH)

BLOG_DIR     = paths.BLOG_DIR
DAILY_QUOTA  = int(os.getenv("DAILY_QUOTA", "5"))

# ── 마크다운 렌더링 버그 수정 ──────────────────────────────────
# remark-gfm에서 **숫자.숫자%** 패턴(예: **56.1%**)이 bold로 렌더링 안 되고
# 리터럴 "**56.1%**"로 보이는 버그가 있음. 이 패턴을 찾아 수정.
_BOLD_DECIMAL_PERCENT = re.compile(r'\*\*(\d+\.\d+)%\*\*')

def fix_bold_decimal_percent(text: str) -> str:
    """**42.1%** → **42.1**% 로 변환 (remark-gfm 버그 회피)"""
    return _BOLD_DECIMAL_PERCENT.sub(r'**\1**%', text)

# ── 로컬 로그 설정 ──────────────────────────────────────────
LOG_DIR  = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pipeline")

from shared.db_utils      import (get_pending_count, get_today_published_count,
                                   pick_next_service, get_related_posts,
                                   increment_internal_link_count,
                                   mark_published, mark_error)
from shared.thumbnail_gen import generate as gen_thumbnail
from shared.build_deploy   import run as deploy
from shared.notifier       import send as notify
from shared.reviewer       import review_article
from shared.url_checker    import check_gov24_alive
from shared.naver_validator import check_topic_relevance
from writer     import generate_article, proofread
from validator  import (validate_and_fix, fill_related_posts,
                        make_slug, make_frontmatter,
                        make_persona_cta_block,
                        clean_prompt_leaks)
from fetcher    import fetch_all as fetch_gov24
from fetcher_loan_fin import fetch_all as fetch_finlife
from fetcher_invest    import fetch_all as fetch_invest

with open(os.path.join(os.path.dirname(__file__), "config/category_map.yaml"),
          encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)
CATEGORY_QUOTA  = CONFIG["category_quota"]
PERSONA_CTA     = CONFIG["persona_cta"]
PERSONA_LABELS  = CONFIG.get("persona_labels", {})
CTA_VARIANTS    = CONFIG.get("cta_variants", {})

# ── 뱅크샐러드 스타일 헬퍼 ───────────────────────────────────
def extract_title_from_draft(body: str) -> str | None:
    """LLM output 첫 줄 # 제목 → 제목 문자열 추출 + 마커 태그 제거"""
    first_line = body.split('\n')[0].strip()
    m = re.match(r'^#\s+(.+)$', first_line)
    if not m:
        return None
    title = m.group(1).strip()
    # 마커 태그 제거: [PERSONA_CTA], [RELATED_POSTS], [__MARKER_*]
    title = re.sub(r'\s*\[(?:PERSONA_CTA|RELATED_POSTS|__MARKER_[^\]]*)\]', '', title)
    return title.strip()

_MARKER_IN_H2 = re.compile(r'\[(RELATED_POSTS|PERSONA_CTA|__MARKER_[^\]]+)\]')

def build_summary_box(body: str) -> str:
    """본문 H2 제목 추출 → 목차 박스 생성 (이모지 없음)"""
    h2s = re.findall(r'^##\s+(.+)$', body, re.MULTILINE)
    if not h2s:
        return ""

    items = []
    for i, h2 in enumerate(h2s[:6]):
        if _MARKER_IN_H2.search(h2):
            continue
        anchor = re.sub(r'[^\w\s가-힣]', '', h2.strip()).replace(' ', '-').lower()
        items.append(f"- [{h2}](#{anchor})")

    if not items:
        return ""
    box = "**목차**\n\n"
    for item in items:
        box += f"{item}\n"
    box += "---\n\n"
    return box

# ── 인라인 CTA ────────────────────────────────────────────────
def _inline_cta_label(service: dict) -> str:
    """service → persona_labels 기반 표시명"""
    cat = service.get("category", "general")
    persona = service.get("persona", "general")
    lbl = PERSONA_LABELS.get(cat)
    if isinstance(lbl, str):
        return lbl
    if isinstance(lbl, dict):
        return lbl.get(persona, lbl.get("default", "30대 직장인"))
    return "30대 직장인"

def _ab_index(service_id) -> int:
    """service_id 기반 결정적 A/B 인덱스 (0/1). 재빌드 간 일관성 보장."""
    import hashlib
    sid = str(service_id)
    return int(hashlib.md5(sid.encode("utf-8")).hexdigest(), 16) % 2

def insert_inline_ctas(body: str, service: dict) -> str:
    """조건 섹션 뒤 + 금리 섹션 뒤에 /my-persona CTA 삽입 (variant-driven, A/B)

    미드(in-body, H2#2/H2#3 뒤) = 약함/호기심(mid) 복사.
    END CTA는 validator.make_persona_cta_block에서 end(강함) 변인 사용.
    src 토큰(inline-peer-/inline-stats-)은 그대로 유지 → T5 귀속 파싱 호환.
    """
    h2_starts = [m.start() for m in re.finditer(r'^##\s+', body, re.MULTILINE)]
    if len(h2_starts) < 3:
        return body

    cat = service.get("category", "general")
    persona = service.get("persona", "general")
    key = f"{cat}-{persona}"
    variants = CTA_VARIANTS.get(key, CTA_VARIANTS.get("default", {}))
    mid = variants.get("mid", ["내 또래 평균이 궁금하다면 확인해보세요", "비슷한 조건 사람들은 어떻게 살까요?"])
    idx = _ab_index(service.get("service_id", ""))
    mid_text = mid[idx % len(mid)]

    cta2 = (
        f"\n\n> **{mid_text}**\n"
        f"> 나이·성별·지역만 입력하면 또래 소득·주거·직업 통계를 바로 확인할 수 있습니다.\n"
        f">\n"
        f"> [내 페르소나 통계 보기 →](/my-persona?src=inline-stats-{cat}-{persona})\n"
    )
    cta1 = (
        f"\n\n> **{mid_text}**\n"
        f"> 나와 비슷한 사람들의 평균 소득과 생활 패턴이 궁금하다면?\n"
        f">\n"
        f"> [또래 정보 확인하기 →](/my-persona?src=inline-peer-{cat}-{persona})\n"
    )

    # bottom-up 삽입 (position shift 방지)
    body = body[:h2_starts[3]] + cta2 + body[h2_starts[3]:]
    body = body[:h2_starts[2]] + cta1 + body[h2_starts[2]:]
    return body

def run(dry_run=False):
    logger.info(f"파이프라인 시작 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 오늘 quota 확인
    today_count = get_today_published_count()
    if today_count >= DAILY_QUOTA:
        logger.info(f"오늘 quota 초과 ({today_count}/{DAILY_QUOTA}), 종료")
        return

    remaining = DAILY_QUOTA - today_count
    logger.info(f"오늘 {today_count}건 발행됨, {remaining}건 남음")

    # 2. pending 없으면 재수집 (3개 소스 통합 호출)
    pending = get_pending_count()
    if pending == 0:
        logger.info("pending 없음 → 재수집 시작")
        fetch_gov24()
        fetch_finlife()
        fetch_invest()
        pending = get_pending_count()
        if pending == 0:
            notify("pending 서비스 없음, 파이프라인 종료", "WARN")
            return

    published_count = 0
    for _ in range(remaining):
        # 3. 카테고리 가중치 기반 서비스 선택
        service = pick_next_service(CATEGORY_QUOTA)
        if not service:
            logger.info("선택 가능한 서비스 없음")
            break

        logger.info(f"처리 중: {service['title'][:40]}")

        # 3b. 블로그 부적합 키워드 필터링 (자세한 목록은 AGENTS.md 참조)
        _EXCLUDE_KW = [
            "농업", "어업", "축산", "수산", "임업", "농림",
            "천일염", "포장재", "동물", "백신", "가축",
            "양식", "어가", "영농", "농기계", "비료",
            "종자", "사료", "축사", "수산물",
            "한센", "수술비", "치매", "백내장", "임플란트",
            "발달장애", "학대피해", "보호종료", "가정폭력",
            "북한이탈", "귀화",
            "선원", "어업인", "항로표지", "해양사고",
            "초지", "원산지검증", "유휴간호사",
            "금연", "마약", "결핵",
            "진술조력인", "국선변호사", "법률홈닥터",
            "고위험임산부", "희귀질환", "감염병격리",
            "영양플러스", "방문건강",
            "응시료", "노인안검진", "개안술", "인공관절",
            "장기요양", "낙상방지", "보조기기",
        ]
        title = service.get("title", "")
        field = service.get("field", "")
        target = service.get("target", "")
        summary = service.get("summary", "")
        combined_text = f"{title} {field} {target} {summary}"
        if any(kw in combined_text for kw in _EXCLUDE_KW):
            logger.info(f"[SKIP] 부적합 키워드: {title[:40]}")
            mark_error(service["service_id"], "부적합 키워드")
            continue

        # 3c. URL Alive 검증 (Gov24만)
        source = service.get("source", "")
        if source == "gov24" and service.get("detail_url"):
            if not check_gov24_alive(service["service_id"], service["detail_url"]):
                logger.info(f"[SKIP] URL 비활성: {service['title'][:40]}")
                continue

        # 3d. 관심도 검증 (Finlife, datagokr, income_series)
        if source in ("finlife", "datagokr", "income_series"):
            relevance = check_topic_relevance(service.get("title", ""), service.get("summary", ""))
            if relevance["relevance"] == "none":
                mark_error(service["service_id"], "no_search_results")
                logger.info(f"[SKIP] 검색 결과 없음: {service['title'][:40]}")
                continue
            elif relevance["relevance"] == "stale":
                needs_review = True
                logger.info(f"[WARN] 관심도 낮음 (stale): {service['title'][:40]}")

        # 4. GPT 글쓰기
        if dry_run:
            logger.info(f"[DRY] 글쓰기 스킵 | category={service['category']} | persona={service['persona']}")
            continue

        result = generate_article(service)
        if not result:
            mark_error(service["service_id"], "GPT 실패")
            notify(f"GPT 실패: {service['title'][:30]}", "WARN")
            continue

        body = result["body"]
        model_used = result.get("model", "unknown")

        # 4a. 출력 후 교정기 (맞춤법·문법)
        body = proofread(body)

        # 4b. LLM output → 제목 추출 (Q3)
        extracted_title = extract_title_from_draft(body)
        if extracted_title:
            body = re.sub(r'^#\s+.*?\n?', '', body, count=1).strip()
            logger.info(f"제목 추출: {extracted_title[:40]}")
        final_title = extracted_title or service["title"]
        # 타이틀 생성기로 마무리 어미 다양화 (신규 글만 해당)
        final_title = refinish_title(final_title)
        logger.info(f"refinish_title 적용: {final_title[:50]}")

        # 4c. (비활성화) H2 기반 SUMMARY_BOX — BlogPost.astro 자체 TOC로 대체
        # summary_box = build_summary_box(body)
        # if summary_box:
        #     body = summary_box + '\n' + body

        # 4d. 인라인 CTA 삽입 (조건 섹션 뒤 + 금리 섹션 뒤)
        body = insert_inline_ctas(body, service)

        # 5. reviewer (Mimo v2.5 검수 + 마커 보호/복원)
        body, review_issues, needs_review = review_article(body, model_used)
        if review_issues:
            logger.info(f"[reviewer] {review_issues}")

        # 5b. validator (CTA 강제 삽입 + 헤딩 검증)
        persona = service.get("persona", "default")
        cat = service.get("category", "general")
        cta_url = PERSONA_CTA.get(persona, PERSONA_CTA.get("default", "https://persona.aikorea24.kr/my-persona"))
        _vkey = f"{cat}-{persona}"
        _v = CTA_VARIANTS.get(_vkey, CTA_VARIANTS.get("default", {}))
        _end = _v.get("end", ["내 또래는 어떤 혜택을 받고 있을까?"] * 2)
        _idx = _ab_index(service.get("service_id", ""))
        _end_text = _end[_idx % len(_end)]
        cta_block = make_persona_cta_block(cta_url, persona=persona, end_text=_end_text)
        body, issues = validate_and_fix(body, cta_url, cta_block=cta_block)
        if "BODY_TOO_SHORT" in issues:
            mark_error(service["service_id"], "본문 너무 짧음")
            continue
        if issues:
            logger.info(f"[validator] 수정됨: {issues}")

        # 5c. 마크다운 bold+소수점+% 버그 수정 (**42.1%** → **42.1**%)
        body = fix_bold_decimal_percent(body)

        # 6. slug 생성
        slug = make_slug(final_title, service["service_id"])

        # 7. RELATED_POSTS 채우기 (내부 링크 균등 분배)
        related = get_related_posts(service["category"], slug)
        body = fill_related_posts(body, related)
        for post in related:
            increment_internal_link_count(post["slug"])

        # 8. 썸네일 생성 + R2 업로드
        hero_image = gen_thumbnail(slug, final_title, service["category"])
        if not hero_image:
            hero_image = f"https://pub-2f5c7af1c303419a933069212bc25874.r2.dev/blog-thumbnails/default.jpg"

        # 9. 프론트매터 + 본문 조합
        cat = service["category"]
        tag_suffix = {"invest": ["투자", "ETF"], "tax": ["세금", "절세"]}.get(cat, ["지원금", "혜택"])
        tags = [cat, service.get("persona","")] + tag_suffix
        tags = [t for t in tags if t]
        description = service.get("summary","")[:120]
        frontmatter = make_frontmatter(
            final_title, description,
            service["category"], hero_image, tags, slug,
            needs_review=needs_review
        )
        final_md = frontmatter + body

        # 10. 파일 저장
        out_path = os.path.join(BLOG_DIR, f"{slug}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(final_md)
        logger.info(f"저장: {out_path}")

        # 11. DB 기록
        mark_published(service["service_id"], slug,
                       final_title, service["category"],
                       service.get("persona",""),
                       model_used=result.get("model",""))
        published_count += 1
        logger.info(f"발행 성공: {final_title[:40]} | {service['category']} | {model_used}")

    # 12. 빌드 + 배포
    if published_count > 0:
        logger.info(f"{published_count}건 발행 → 빌드/배포 시작")
        ok, detail = deploy(published_count)
        if ok:
            logger.info(f"배포 완료 ({published_count}건)")
        else:
            logger.error(f"빌드/배포 실패 ({published_count}건 저장됨)\n{detail}")
            notify(f"빌드/배포 실패 ❌ ({published_count}건 저장됨)\n\n```\n{detail[:800]}\n```", "ERROR")
    else:
        logger.info("발행 없음")

    logger.info(f"파이프라인 종료 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run(dry_run=dry_run)
