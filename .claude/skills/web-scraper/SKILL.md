---
name: web-scraper
description: Capture external pages into the wiki - a single URL, a whole documentation site, or a PDF. Handles JavaScript-rendered pages, thin-content detection, and Hebrew/RTL PDFs. Load when the user wants to scrape, capture, or import outside material as persistent knowledge.
---

# Web and PDF Capture

Two scripts turn outside material into markdown the wiki can hold. Both write
into `wiki/sources/`, which is raw captured text - not wiki pages. Turning a
source into a wiki page is `/wiki-ingest`.

Read `wiki-kit.json` first for the `python` path and `scripts_dir`. Below,
`PY` means that interpreter and `S` means the scripts directory.

If `python` is `null`, neither script can run - this project was installed
without Python. Stop here and follow "When `python` is `null`" in
`.claude/skills/wiki/SKILL.md`. Nothing on this page works until that is
resolved.

---

## One page

```bash
PY S/scrape_web.py --url "<url>" --slug "<short-name>"
```

- `slug` is a lowercase-hyphenated filename without `.md`. Omit it and one is
  derived from the URL.
- Output: `wiki/sources/web/<site>/<slug>.md`, where `<site>` is the URL's host
  (`docs.canva.com` becomes `docs-canva-com`). You do not pass it and you do not
  coordinate it - every page of one site groups itself, which is what keeps a
  thirty-page scrape from becoming thirty loose files in one folder.
- `--collection NAME` overrides that folder. Use it when one body of knowledge
  is spread over several hosts (`docs.x.com` and `api.x.com`), so it arrives as
  one collection instead of two.
- `--flat` writes straight into `wiki/sources/web/`, no subfolder.
- `--out DIR` writes to an exact directory and ignores the two flags above.

**Thin output.** Under 150 words, the script says so. Two possible reasons: the
page is genuinely short, or it is a JavaScript shell that needs a real browser.
If Playwright is installed it retries automatically; otherwise **read the file
before ingesting it**. Never ingest a source you have not opened.

**Forcing a browser:** `--playwright`. Requires the Playwright extra
(`python wiki-kit/install.py --with-playwright`).

---

## A PDF

```bash
PY S/convert_pdf_to_md.py --pdf "<path/to/file.pdf>" --slug "<short-name>"
```

- Output: `wiki/sources/pdf/<slug>.md`
- Headings are recovered from font sizes, so structure usually survives.

**Two failure modes worth knowing:**

1. **Scanned PDF.** Image-only files have no text layer. The script reports
   thin output. Nothing can be recovered without OCR, which is not included -
   tell the user rather than ingesting an empty page.
2. **Reversed Hebrew.** PDFs store text visually, and some producers emit
   right-to-left runs backwards. The script warns when it detects this. Re-run
   with `--fix-rtl` and compare the two outputs by eye. Pick the one that reads
   correctly; do not guess.

---

## A whole documentation site

Try these in order and stop at the first that works - each is cheaper than the
next.

**1. Markdown shortcut.** Many docs platforms serve a clean markdown version of
any page when `.md` is appended to its URL. Test one page with `curl`. If it
returns markdown, you never need a scraper.

**2. Sitemap.** Fetch `<site>/sitemap.xml` and filter the URLs by path. Most
sites have one, and it is a complete list rather than whatever the nav shows.

**3. Spider (needs Playwright).**
```bash
PY S/spider_docs_urls.py "<start-url>" "<path-filter>"
```
Start from a page with the full navigation visible. `path-filter` is a substring
every wanted URL contains, e.g. `docs/` or `api-reference`. Add `--deep 20` when
the nav only reveals the current section.

**Then scrape the list**, pausing between requests so the site is not hammered:

```bash
while read -r url; do
  slug=$(echo "$url" | sed 's|.*/||')
  PY S/scrape_web.py --url "$url" --slug "$slug" --no-fallback
  sleep 0.5
done < urls.txt
```

Every page lands in the same `sources/web/<site>/` folder on its own, because
each run derives that folder from its own URL. Pass `--collection NAME` on every
line of the loop only if you want a name of your choosing, or if the URLs span
more than one host and belong together anyway.

Review the URL list before scraping it. A 300-page docs site scraped blindly
produces 300 files nobody will read.

---

## After capturing

Sources are not knowledge yet. Run `/wiki-ingest` to synthesize them into wiki
pages. For a multi-page capture, do not create one wiki page per scraped page:
write one hub page plus a few family pages, all cross-linked. Ten good pages
beat three hundred transcriptions.
