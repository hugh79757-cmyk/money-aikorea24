#!/usr/bin/env python3
"""CI content generator — run pipeline without build/deploy.

Used by GitHub Actions to generate content, then git commit/push.
Cloudflare Pages handles build+deploy on push.

Usage:
    python3 ci_generate.py           # generate + git commit
    python3 ci_generate.py --dry-run # generate only, no commit
"""

import os, sys, subprocess, json
from pathlib import Path
from datetime import datetime

# Ensure auto-writer AND scripts/ are on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))          # auto-writer/ (pipeline, etc.)
sys.path.insert(0, str(SCRIPT_DIR.parent))   # scripts/ (paths.py)

import paths


def run_check_fix():
    """Run check-blog-issues.py --fix to clean up issues before pipeline."""
    print("[ci] Running check-blog-issues.py --fix ...")
    result = subprocess.run(
        [sys.executable, str(Path(paths.SCRIPTS_DIR) / "check-blog-issues.py"), "--fix"],
        cwd=paths.PROJECT_ROOT,
        capture_output=True, text=True, timeout=120
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"[ci] WARNING: check-blog-issues.py exited {result.returncode}")
        print(result.stderr)
    return result.returncode


def run_pipeline(dry_run=False):
    """Run pipeline.py:run(deploy_enabled=False) — generate content only."""
    print(f"[ci] Running pipeline (dry_run={dry_run}) ...")
    from pipeline import run as pipeline_run
    pipeline_run(dry_run=dry_run, deploy_enabled=False)
    print("[ci] Pipeline complete.")


def git_commit_push():
    """Stage, commit, and push all changes."""
    print("[ci] Checking for changes ...")

    # Check if there are any changes
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=paths.PROJECT_ROOT, capture_output=True, text=True
    )
    if not status.stdout.strip():
        print("[ci] No changes to commit.")
        return

    # Stage all changes (new .md files, DB updates, etc.)
    subprocess.run(
        ["git", "add", "-A"],
        cwd=paths.PROJECT_ROOT, check=True
    )

    # Commit
    today = datetime.now().strftime("%Y-%m-%d")
    commit_msg = f"content: auto-generate {today}"
    subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=paths.PROJECT_ROOT, check=True
    )
    print(f"[ci] Committed: {commit_msg}")

    # Push
    print("[ci] Pushing to origin ...")
    result = subprocess.run(
        ["git", "push", "origin", "HEAD"],
        cwd=paths.PROJECT_ROOT,
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"[ci] Push failed:\n{result.stderr}")
        sys.exit(1)
    print("[ci] Push complete.")


def main():
    dry_run = "--dry-run" in sys.argv

    # Step 1: Fix blog issues
    run_check_fix()

    # Step 2: Run pipeline (content generation only, no build/deploy)
    run_pipeline(dry_run=dry_run)

    # Step 3: Git commit + push (triggers Cloudflare Pages build+deploy)
    if not dry_run:
        git_commit_push()

    print(f"\n[ci] Done. {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
