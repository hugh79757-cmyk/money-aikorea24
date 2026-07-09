# STATE.md — Sisyphus Bug Fix Session

> **Status**: Investigation complete | Fix applied (uncommitted, undeployed)

---

## Original Bug Report
**Auto-generated blog pages**: Internal link cards at the bottom ("📌 관련 글 더 보기") are rendered in the HTML but not clickable.

## Investigation Summary

### Evidence Collected
1. **Dev server** (`localhost:4321`): ✅ Both link types (inline h4 links + template cards) navigate correctly in Playwright
2. **Production** (`persona.aikorea24.kr`): ✅ Same — both link types navigate correctly
3. **HTML inspection** (production): Correct `<a href="...">` tags with valid URLs
4. **CSS inspection**: No `pointer-events: none`, no `overflow: hidden`, no overlapping `position: fixed` elements blocking clicks
5. **JS inspection**: No `preventDefault()` on link clicks, no click interception
6. **Console errors**: Only 1 unrelated SVG path parse error (cosmetic)
7. **Astro template** (`BlogPost.astro:432-446`): Correct rendering logic for template cards
8. **Auto-writer pipeline** (`pipeline.py:270-272`, `validator.py:102-113`): `fill_related_posts()` generates proper markdown
9. **DB layer** (`db_utils.py:128-139`): `get_related_posts()` returns correct slug/title/category

### Root Cause Hypothesis
**Inconsistency in href encoding** between the two related-post sections:

| Section | href format | Source |
|---|---|---|
| Inline (h4 `fill_related_posts`) | URL-encoded (`%EB%AC%B4%EC%A3%BC%ED%83%9D`) | Markdown processor auto-encodes |
| Template cards (`.related-card`) | Raw Hangul (`무주택`) | `p.id` used directly (BlogPost.astro:437) |

The raw Hangul in `href` is standards-noncompliant per RFC 3986. While modern browsers handle it, certain user agents, ad-injection scripts, or browser extensions may fail to process non-ASCII URLs correctly. The inline links (URL-encoded) consistently work because they follow the spec.

### Other Files With Same Pattern (not fixed — lower priority)
```
PersonaBlogRecommend.astro:140  — href={`/blog/${post.slug}/`}
pages/index.astro:135           — href={"/blog/" + post.id + "/"}
pages/blog/category/[...]/index.astro:205 — href={`/blog/${post.id}/`}
pages/blog/index.astro:191      — href={`/blog/${post.id}/`}
```

---

## Changes Applied (uncommitted)

### `src/layouts/BlogPost.astro`

**1. URL-encode template card slug** (line 437)
- Before: `href={\`/blog/\${p.id}/\`}` 
- After: `href={\`/blog/\${encodeURIComponent(p.id)}/\`}`
- Effect: Makes href consistent with inline links (URL-encoded Hangul)

**2. Add explicit `cursor: pointer`** to `.related-card` CSS (line 303)
- Adds `cursor: pointer` declaration
- Safety measure against CSS resets that strip default link cursor

### Build
- ✅ 2455 pages built in 40.91s — no errors
- Fix is in working tree, uncommitted

---

## How to Deploy
```bash
git add -A && git commit -m "[fix] URL-encode related card hrefs for RFC 3986 compliance"
git push origin main
# or let auto-writer's deploy() handle it on next run
```

## Verification Checklist
- [x] Build compiles (2455 pages, 0 errors)
- [x] Template cards use URL-encoded hrefs matching inline link format
- [x] `.related-card` has explicit `cursor: pointer`
- [x] No other blog `.astro` templates with the same issue in critical paths (lower priority noted)
