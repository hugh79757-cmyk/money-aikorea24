#!/usr/bin/env python3
"""
Persona Publisher — 메인 파이프라인
실행: .venv/bin/python publisher.py
"""
import os
import shutil
import sys
from datetime import datetime

# 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# .env → .env.common 폴백 로드 (모든 하위 모듈이 사용)
sys.path.insert(0, os.path.join(SCRIPT_DIR, ".."))
from load_env import env  # noqa: F401

BLOG_DIR = "/Users/twinssn/projects/money-aikorea24/src/content/blog"

import watcher
import filter as finance_filter
import classifier
import transformer
import thumbnail
import entity_injector
import validator
import deployer


def slug_from_filepath(filepath: str) -> str:
    return transformer.slug_from_filename(filepath)


def resolve_dst_path(slug: str) -> str:
    dst = os.path.join(BLOG_DIR, f"{slug}.md")
    if not os.path.exists(dst):
        return dst
    # 충돌 시 _2, _3 suffix
    for i in range(2, 99):
        candidate = os.path.join(BLOG_DIR, f"{slug}_{i}.md")
        if not os.path.exists(candidate):
            return candidate
    return dst


def run():
    print(f"\n{'='*50}")
    print(f"[publisher] 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # STEP 1: 신규 파일 감지
    new_files = watcher.get_new_files()
    print(f"[step1] 신규 파일: {len(new_files)}개")

    if not new_files:
        print("[publisher] 새 파일 없음 — 종료 (빌드 스킵)")
        return

    published = []

    for filepath in new_files[:1]:  # 1회 실행 시 1개만 처리
        fname = os.path.basename(filepath)
        print(f"\n--- 처리 중: {fname}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = f.read()

            # STEP 2: 카테고리 분류
            category, needs_review = classifier.classify(raw)
            print(f"  [step3] 카테고리: {category} (needs_review={needs_review})")

            # STEP 4: frontmatter 변환
            transformed = transformer.transform(filepath, category, needs_review)
            slug = slug_from_filepath(filepath)
            print(f"  [step4] 변환 완료 (slug={slug})")

            # STEP 4.1: slug 정규화 (NFD → NFC, 공백 → 하이픈)
            normalized_slug = validator.normalize_slug(slug)
            if normalized_slug != slug:
                print(f"  [step4.1] slug 정규화: '{slug}' → '{normalized_slug}'")
                slug = normalized_slug

            # STEP 4.2: frontmatter 타입 검증 + auto-fix
            validated_content, fixes = validator.validate_and_fix_content(transformed)
            if fixes:
                print(f"  [step4.2] auto-fix 적용 ({len(fixes)}건):")
                for f in fixes:
                    print(f"    - {f}")
                transformed = validated_content

            # STEP 4.5: title 기반 중복 체크
            fm, _ = transformer.extract_frontmatter(transformed)
            title = fm.get("title", slug)
            _dup = False
            for _ef in os.listdir(BLOG_DIR):
                if not _ef.endswith('.md'): continue
                try:
                    _ec = open(os.path.join(BLOG_DIR, _ef), encoding='utf-8').read()
                    _efm, _ = transformer.extract_frontmatter(_ec)
                    if _efm.get("title", "").strip() == title.strip():
                        print(f"  [step4.5] 중복 발견: {title[:40]}... → 기존 slug 유지, 스킵")
                        watcher.mark_done(fname, "duplicate_skip", category=category, existing_slug=_ef.replace('.md',''))
                        _dup = True
                        break
                except: continue
            if _dup:
                continue

            # STEP 5: 썸네일 생성
            thumb_path = thumbnail.generate(slug, title, category)
            print(f"  [step5] 썸네일: {os.path.basename(thumb_path)}")

            # STEP 6: 엔티티 링크 삽입
            transformed = entity_injector.inject(transformed, category, current_slug=slug)
            print(f"  [step6] 엔티티 주석 삽입")

            # STEP 7: blog/ 복사
            dst_path = resolve_dst_path(slug)
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(transformed)
            print(f"  [step7] 복사: {os.path.basename(dst_path)}")

            # 발행 완료 파일을 inbox/YYYYMMDD/ 로 이동
            try:
                src_path = filepath
                date_folder = os.path.join(os.path.dirname(src_path), datetime.now().strftime("%Y%m%d"))
                os.makedirs(date_folder, exist_ok=True)
                dst_path = os.path.join(date_folder, fname)
                if os.path.exists(dst_path):
                    os.unlink(dst_path)
                shutil.move(src_path, dst_path)
                print(f"  [move] {fname} → {os.path.basename(date_folder)}/")
            except Exception as _me:
                print(f"  [move 실패] {fname}: {_me}")

            published.append(fname)
            watcher.mark_done(
                fname, "published",
                category=category,
                slug=slug,
                published_at=datetime.now().isoformat(),
            )

        except Exception as e:
            print(f"  [ERROR] {fname}: {e}")
            watcher.mark_done(fname, "error", reason=str(e))
            continue

    print(f"\n[publisher] 처리 완료: {len(published)}개 발행 대상")

    if not published:
        print("[publisher] 발행할 파일 없음 — 빌드 스킵")
        return

    # STEP 8: 빌드 + 배포
    success = deployer.build_and_deploy(len(published))
    if not success:
        print("[publisher] 배포 실패")
        return

    print(f"[publisher] 완료: {len(published)}개 글 발행")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    run()
