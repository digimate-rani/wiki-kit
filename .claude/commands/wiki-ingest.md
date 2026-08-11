---
description: Add a source to the wiki - a URL, a PDF, or a note. Converts it to markdown, synthesizes a wiki page, and updates the index and log.
---

# /wiki-ingest

<when_to_use>
- The user drops a URL, a PDF path, or a local `.md` file
- The user says "add this to the wiki", "save this", "remember this", "document this"
- Something worth keeping happened and should outlive the session
</when_to_use>

<setup>
Read `wiki-kit.json` at the project root. It gives you `python`, `wiki_root`
and `scripts_dir`. Run every script with that `python`, not a bare `python`.
Below, `wiki/` means `wiki_root`.
</setup>

<steps>

## 1. Work out what kind of source this is

| Input | Type |
|-------|------|
| Path ending in `.pdf` | **PDF** |
| Any URL | **Web page** |
| Path ending in `.md`, or "write a note about X" | **Note** |

## 2. Convert it into `wiki/sources/`

**PDF - always convert before anything else. Never read a PDF straight into a wiki page.**
```bash
<python> <scripts_dir>/convert_pdf_to_md.py --pdf "<path>" --slug "<slug>"
```
Then check the script's output:
- It warned about **thin output** → the PDF is probably scanned. Say so and stop.
  OCR is not part of this kit. Do not invent content to fill the gap.
- It warned about **reversed Hebrew** → re-run with `--fix-rtl`, open both files,
  and keep whichever reads correctly. If you cannot tell, show the user both and ask.

**Web page**
```bash
<python> <scripts_dir>/scrape_web.py --url "<url>" --slug "<slug>"
```
Thin output means either a short page or a JavaScript shell. Open the file and
judge before continuing.

**Note**
- A file path the user gave you: read it directly, no conversion.
- "Write a note about X": write it yourself, then save a copy to
  `wiki/sources/local/<slug>.md`. Cover what happened, the decisions made, what
  worked, and paths to the real files.

`slug` = short, lowercase, hyphenated. No dates unless the date is the point.

## 3. Read `wiki/index.md`

**Mandatory, before touching any wiki file.** It tells you which categories
exist, which pages already exist (so you do not duplicate), and which entity
pages to update rather than recreate.

## 4. Read the converted source in full

All of it. A page synthesized from a skim is worse than no page, because it
looks authoritative.

## 5. Decide what to write

- **Category**: pick from the ones in `index.md`. Do not invent a new category
  without asking. If two fit, pick the one where someone would look first.
- **New pages**: usually one summary page. Add concept or entity pages only when
  the concept will recur across sources.
- **Existing pages to update**: anything the index shows covering the same
  ground - update it instead of writing a near-duplicate.

## 6. Say the plan out loud, in one message

> "Found: [2-3 key takeaways]. I'll create [X] and update [Y]. OK?"

Wait for confirmation. **Skip this step only when called from
`/wiki-ingest-batch`**, where confirmation happens once for the whole batch.

## 7. Write the pages

Every page, new or updated, opens with frontmatter:

```markdown
---
title: "Page Title"
date: "YYYY-MM-DD"
sources: ["wiki/sources/<type>/<slug>.md"]
related: ["<category>/<related-page>.md"]
---
```

All four fields are required. `related:` lists the same pages as the `##
Related` section at the bottom, written as paths from the wiki root, and it is
the field most often left as `[]` by accident. An empty `related:` on a page
that does have links in its body is wrong, and it reads as "this page connects
to nothing" in any tool that displays the frontmatter. Fill it, or the page
looks isolated even though it is not.

Then the content. Synthesize, do not transcribe: what is true, what it means
here, what to do with it. If the source is a reference, tables and copy-paste
snippets beat prose.

### Links - one standard, no exceptions

- Two places record a connection, and they must agree: the `## Related` section
  in the body holds the real links, and `related:` in the frontmatter lists the
  same pages as metadata. Writing one without the other is the most common way a
  connected page ends up looking orphaned.
- Relative markdown links only: `[Page Title](other-page.md)` in the same folder,
  `[Page Title](../people/name.md)` across folders.
- Never absolute paths (`file:///`, `D:/...`). They break on every other machine.
- Never `[[Wikilinks]]`. They resolve to nothing; filenames are kebab-case.
  To show that syntax as an example, wrap it in backticks.

### No orphans - mandatory

Every new page must get at least one **inbound** link from an existing page.
Add it to that page's `## Related` section in the same ingest.

For a multi-page family (one source producing three or more pages): pick one hub
page, link hub → every family page, and every family page → hub and its siblings.
An unlinked family is invisible the moment you forget it exists.

## 8. Update `wiki/index.md`

One line per new page, under its category:
```
- [Page Title](category/slug.md) - one line description *(Sources: N, Updated: YYYY-MM-DD)*
```
For an updated page: increment the source count and change the date.

## 9. Append `wiki/log.md`

```
## [YYYY-MM-DD] ingest | <source title>

Source: <web|pdf|note> - <path>
Pages touched: <list>
Key insight: <one line>
```

## 10. Confirm

> "Done. Created: [X]. Updated: [Y]. Key insight: [one line]."

</steps>

<rules>
- `index.md` is read first. Always.
- One source per ingest. Finish it completely before starting another.
- PDFs are converted by the script first - never summarized straight from the binary.
- Warnings from the conversion scripts are reported to the user, not swallowed.
- Never create a second entity page for something that already has one.
- Every page has all four frontmatter fields. `related: []` is only correct on a
  page that genuinely has no `## Related` links - which should be rare.
- Every new page has an inbound link.
- Every ingest touches `index.md` and `log.md`. No exceptions.
- Wiki pages are written in the language of the source; the conversation follows the user.
</rules>
