---
description: Ingest everything waiting in wiki/inbox/ - notes, PDFs and a URL list - in one pass, then archive each processed file.
---

# /wiki-ingest-batch

<when_to_use>
- The user says "ingest the inbox", "process the queue", "add all of these"
- Several sources piled up and ingesting them one at a time would be tedious
</when_to_use>

<setup>
Read `wiki-kit.json` for `python`, `wiki_root` and `scripts_dir`.
Below, `wiki/` means `wiki_root`.
</setup>

<steps>

## 1. Scan the inbox

List everything in `wiki/inbox/`, excluding `done/` and `README.md`:

- `.md` files → notes, ready as-is
- `.pdf` files → need conversion first
- `urls.txt` → one URL per line, each needs scraping

Empty inbox → say "Nothing in the inbox" and stop.

## 2. Read `wiki/index.md` once, and skim the queue

Read the index in full. Read only the **title and first section** of each queued
file - enough to decide its category and page plan. The full read happens later,
inside each item's own pass.

## 3. Build the plan

For each item decide: category, pages to create, pages to update.

## 4. One grouped confirmation

> **N items** ready to ingest:
>
> | # | Item | Type | Category | Create | Update |
> |---|------|------|----------|--------|--------|
> | 1 | `claude-code-tips.md` | note | learning | `learning/claude-code-tips.md` | - |
> | 2 | `pricing-guide.pdf` | pdf | knowledge | `knowledge/pricing-model.md` | `people/vendor.md` |
>
> Confirm, or adjust any row.

Wait. Ask once for the whole batch, never per item.

## 5. Process one item at a time - strictly sequential

Every item shares `index.md`, `log.md` and the entity pages. Two writers on the
same file means one of them loses. **Never run these in parallel.**

For each item, in order:

1. **Convert if needed.**
   - PDF: `<python> <scripts_dir>/convert_pdf_to_md.py --pdf "<path>" --slug "<slug>"`
   - URL: `<python> <scripts_dir>/scrape_web.py --url "<url>" --slug "<slug>"`
   - Note: no conversion.
2. **Read the source in full.**
3. **Re-read `wiki/index.md` from disk** - it now includes what the previous
   items wrote.
4. **Write the pages** following every rule in `/wiki-ingest` step 7: frontmatter,
   relative links, at least one inbound link, no duplicate entity pages.
5. **Update `index.md`** - add or increment the entry.
6. **Append `log.md`:**
   ```
   ## [YYYY-MM-DD] ingest | <title>

   Source: <web|pdf|note> - inbox/<filename>
   Pages touched: <list>
   Key insight: <one line>
   ```
7. **Archive the file**: move it to `wiki/inbox/done/`. Immediately - not at the
   end of the batch. A crash halfway through must not re-ingest what already
   landed. (For `urls.txt`, move the whole file only after every URL in it is done.)

If one item fails: report it, leave that file in the inbox, and continue with
the rest. One bad PDF does not abort a batch of twelve.

## 6. Final report

> Done. Ingested **N of M** items.
>
> Pages created: X | updated: Y
> - [Title] → `wiki/<category>/<slug>.md`
>
> Failed: <item + one-line reason, or "none">
> Processed files archived to `wiki/inbox/done/`.

</steps>

<rules>
- Strictly sequential. Shared files make parallel ingestion a corruption bug.
- Re-read `index.md` from disk before each item - not from memory.
- One confirmation for the whole batch, before any writing starts.
- Archive each file the moment it succeeds; leave failures in place.
- A failed item is reported, not silently dropped, and never abandons the batch.
- Warnings from the conversion scripts (thin PDF, reversed Hebrew) surface in
  the final report.
- All the `/wiki-ingest` writing rules apply unchanged.
</rules>
