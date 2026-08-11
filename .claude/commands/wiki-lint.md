---
description: Health-check the wiki - orphan pages, index drift, broken links, missing cross-references, concept gaps, stale claims. Produces a report and fixes only what is approved.
---

# /wiki-lint

<when_to_use>
- "Lint the wiki", "health-check the wiki", "clean up the wiki"
- After a large batch ingest
- Every 20-30 new sources, as maintenance
</when_to_use>

<steps>

## 1. Read `wiki/index.md`

Your map of what is supposed to exist.

## 2. Read every wiki page

All `.md` files under `wiki/`, excluding `index.md`, `log.md`, `sources/` and
`inbox/`. This is the one workflow that reads the whole wiki - that is why it is
occasional maintenance, not something to run casually.

If the wiki is large (over ~60 pages), lint one category at a time and say which
one you covered.

## 3. Run the six checks

### A - Orphan pages
A page no other page links to. List every one.

### B - Index drift and broken links
Both directions: pages on disk missing from `index.md`, and index entries
pointing at files that do not exist. Then link hygiene inside pages: absolute
`file:///` or drive-letter paths, relative paths that resolve to nothing, and
`[[Wikilink]]` syntax matching no filename.

### C - Missing cross-references
Pages that clearly belong together and do not link to each other. Name the pair
and the reason.

### D - Concept gaps
Terms, tools or people mentioned across three or more pages with no page of
their own. Top 5 only.

### E - Stale claims
Read `log.md` for ingestion order. Find claims in older pages that newer pages
contradict or supersede. These are the dangerous ones - a wrong page is worse
than a missing page, because it gets trusted.

### F - Thin or transcribed pages
Pages under ~100 words with no real synthesis, or pages that are a raw dump of a
source rather than knowledge. They cost tokens on every index read and give
nothing back.

## 4. Write the report

```markdown
# Wiki Lint Report - YYYY-MM-DD

## Summary
Pages scanned: N | Orphans: N | Drift/broken: N | Missing refs: N
Concept gaps: N | Stale claims: N | Thin pages: N

## A - Orphan pages
- `wiki/category/page.md` - no inbound links

## B - Index drift and broken links
- `wiki/learning/thing.md` exists on disk but is not in the index
- Index points to `wiki/research/gone.md` - file does not exist
- `wiki/knowledge/api.md` links to `file:///D:/...` - absolute path

## C - Missing cross-references
- `wiki/learning/a.md` → should link to `wiki/learning/b.md` (both cover X)

## D - Concept gaps
1. **term** - mentioned in 4 pages. Suggested: `wiki/learning/term.md`

## E - Stale claims
- `wiki/knowledge/x.md` claims "no scheduling support" - contradicted by
  `wiki/knowledge/y.md` (ingested later)

## F - Thin pages
- `wiki/research/z.md` - 60 words, transcription not synthesis
```

Save it to `wiki/lint-report-YYYY-MM-DD.md`.

## 5. Show the report and ask what to fix

> Which do you want me to fix now?
> - A + C: add the missing links
> - B: fix index drift and broken links
> - E: update the stale claims
> - F: rewrite or delete the thin pages
> - D: needs new sources - I'll flag them as research leads
> - All of it / just save the report

## 6. Fix only what was approved

- **Orphans and missing refs (A, C):** add the link to the most relevant existing
  page's `## Related` section. Nothing else in that page changes.
- **Drift (B):** add missing index entries, remove entries whose file is gone,
  rewrite bad links as relative markdown links.
- **Stale claims (E):** update the outdated passage. Keep whatever was still
  true, and note when the change happened if the old claim was true at the time.
- **Thin pages (F):** ask per page - rewrite from the original source, or delete.
  Never quietly pad it out with general knowledge.
- **Concept gaps (D):** do **not** write these pages from general knowledge. Add
  each as a flagged comment in `index.md` under its category:
  ```
  <!-- RESEARCH LEAD: term - mentioned in 4 pages, no dedicated page yet -->
  ```

## 7. Append `wiki/log.md`

```
## [YYYY-MM-DD] lint | Wiki health check

Pages scanned: N
Found: orphans (N), drift (N), missing refs (N), gaps (N), stale (N), thin (N)
Fixed: <list, or "none - report only">
Research leads added: <list, or "none">
```

## 8. Confirm

> "Lint complete. Found X issues, fixed Y. Report saved to `<path>`.
> Research leads flagged: [list]."

</steps>

<rules>
- Read `index.md` first, always.
- Never create a wiki page from general knowledge. A concept gap without a source
  stays a gap - that is what makes the wiki trustworthy.
- Fix only what was explicitly approved. Never silently edit pages during a
  health check.
- Fixing a stale claim preserves whatever part of it was accurate.
- The log entry is mandatory, even for a report-only run.
- Research leads go into `index.md` as HTML comments: the agent sees them on the
  next read, and they stay invisible in any markdown preview.
</rules>
