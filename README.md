# Wiki Kit

Give Claude Code a memory that survives between sessions.

Every session, Claude starts from nothing. You paste the same context again,
re-explain the same decisions, re-find the same documentation. A wiki fixes that:
Claude writes what it learns into markdown files, indexes them, and reads only
what a question actually needs.

This kit installs the whole thing into any project in one command.

---

## What you get

**A wiki folder** with categories you choose, an index, and a log of everything
that ever went in.

**Two capture scripts**

| Script | What it does |
|--------|--------------|
| `scrape_web.py` | Any URL → clean markdown. Strips navigation, ads and cookie banners. Falls back to a real browser for JavaScript-heavy pages. |
| `convert_pdf_to_md.py` | Any PDF → markdown, headings included. Detects scanned files and reversed Hebrew text. |

**Six slash commands**

| Command | What it does |
|---------|--------------|
| `/wiki-query` | Answer a question using the wiki. Reads the index, then 3-5 pages. Never the whole thing. |
| `/wiki-ingest` | Add a URL, a PDF or a note. Converts it, writes a page, updates the index. |
| `/wiki-ingest-batch` | Process everything sitting in `wiki/inbox/` in one pass. |
| `/wiki-lint` | Health check: orphan pages, broken links, stale claims, thin pages. |
| `/wiki-delete` | Remove a page and clean up after it. |
| `/wiki-setup` | Install, add a category, or verify the installation. |

**Three skills** that teach Claude how to use all of it, plus a section added to
your `CLAUDE.md` so Claude knows the wiki exists in the first place.

---

## Requirements

- **Python 3.9 or newer.** Check with `python --version`.
  Windows: install from [python.org](https://www.python.org/downloads/) and tick
  "Add Python to PATH".
- **Claude Code**, in a project folder.
- Nothing else. The installer creates its own isolated environment.

---

## Install

### Step 1 - get the kit into your project

You need a `wiki-kit/` folder sitting inside your project. Either:

```bash
git clone https://github.com/digimate-rani/wiki-kit.git
```

or just copy the `wiki-kit` folder in, if you were handed it directly.

### Step 2 - let Claude install it

Open Claude Code in your project and say:

```
Read wiki-kit/INSTALL.md and follow it
```

Claude asks which wiki folders you want, then does the rest: creates the wiki,
installs the tools, wires up the commands, and runs a self-test.

### Step 3 - restart Claude Code

New slash commands are picked up at startup. Restart the session, then try:

```
/wiki-ingest https://a-page-you-care-about.com
/wiki-query what do we know about it?
```

---

### Prefer to do it yourself?

One command, no agent involved:

```bash
python wiki-kit/install.py
```

It asks which categories you want and installs everything. Useful flags:

```bash
python wiki-kit/install.py --categories "knowledge,learning,research" --yes
python wiki-kit/install.py --with-playwright   # for JavaScript-heavy sites
python wiki-kit/install.py --dry-run           # show the plan, change nothing
python wiki-kit/install.py --verify-only       # re-run the checks
```

---

## What it creates

```
your-project/
├── wiki/
│   ├── index.md            the map - the only file read on every query
│   ├── log.md              append-only history of every change
│   ├── knowledge/          your categories, chosen at install time
│   ├── learning/
│   ├── inbox/              drop files here for /wiki-ingest-batch
│   └── sources/            raw captured text, before it becomes a page
│       ├── web/
│       ├── pdf/
│       └── local/
├── scripts/wiki/           the capture scripts
├── .claude/
│   ├── skills/             wiki, web-scraper, wiki-setup
│   └── commands/           the six slash commands
├── .venv/                  isolated Python environment
├── wiki-kit.json           paths and settings, so every part finds the others
└── CLAUDE.md               gains a short section describing the wiki
```

Re-running the installer is safe. Your pages, index entries and log are never
overwritten - only new category sections get appended.

---

## How to actually use it

**Feed it things you will need twice.** Documentation you keep re-reading, a
client's requirements, how a system you built works, research you would hate to
redo.

**Categories are shelves, not topics.** Four broad ones work. Twenty narrow ones
mean every page becomes a filing decision.

**Trust the index.** Claude reads `index.md` and then only the pages it points
to. That is what keeps a 200-page wiki cheap to query. Do not ask Claude to
"read the whole wiki" - it defeats the design.

**Lint occasionally.** After 20-30 new pages, run `/wiki-lint`. It finds pages
nothing links to, claims newer pages have contradicted, and links that broke.

**Sources are not knowledge.** `wiki/sources/` holds raw captured text.
A wiki page is a synthesis of it. Ingesting without synthesizing gives you a
folder of transcripts and none of the value.

---

## Troubleshooting

**"The slash commands don't exist."**
Restart Claude Code. `.claude/` is read at startup.

**"ModuleNotFoundError" when a script runs.**
The wrong Python was used. The right one is in `wiki-kit.json` under `python` -
the isolated environment, not your system Python.

**A scraped page is nearly empty.**
The site renders with JavaScript. Reinstall with `--with-playwright`, which adds
a real browser (a large one-time download).

**A PDF converted to almost nothing.**
It is a scan - an image with no text layer. This kit does not do OCR.

**Hebrew comes out backwards.**
PDFs store text visually. Re-run the converter with `--fix-rtl` and keep
whichever output reads correctly.

**Check everything at once:**
```bash
python wiki-kit/install.py --verify-only
```

---

## License

MIT. Use it, change it, ship it.
