---
name: wiki-setup
description: Install, extend, verify or repair the project wiki. Use for the first-time setup ("install the wiki", "set up the wiki kit"), for adding a new category later, for re-running the health checks after an error, or when a wiki script fails to run.
---

# Wiki Setup

One installer does the work: `install.py`. Your job is to ask the right
questions first, run it once, and confirm the result honestly.

Talk to the user in whatever language they are writing in.

---

## A. First-time install

### 1. Find the kit and the project

The kit is usually cloned as `<project>/wiki-kit/`. Confirm `install.py` exists
before doing anything else. If the kit is somewhere else, you will pass
`--target <project folder>`.

Check whether it is already installed: if `wiki-kit.json` exists at the project
root, this is not a fresh install - go to section B or C.

### 2. Ask which folders they want

This is the only real decision, and it is theirs. Show the catalog:

```bash
python wiki-kit/install.py --list-categories
```

Present the options in plain language and say what each is for. Explain the
principle in one line: **a category is a shelf, not a topic.** Four broad
shelves work; twenty narrow ones mean every page is a judgement call.

Suggested defaults: `knowledge`, `learning`, `research`, `projects`.

Ask one question, offer the defaults as the easy answer, and accept custom
names. Do not interrogate them section by section.

### 3. Ask about JavaScript-heavy sites

One short question: "Do you need to capture sites that only render with
JavaScript - dashboards, app-like docs? It adds a browser download of a few
hundred megabytes."

Default is no. Most documentation sites scrape fine without it.

### 4. Run the installer

```bash
python wiki-kit/install.py --categories "knowledge,learning,research,projects" --yes
```

Add `--with-playwright` if they said yes in step 3.
Add `--target "<path>"` if the kit is not inside the project.

Never run it without `--categories` unless the user explicitly asked for the
defaults - the flag is how their answer reaches the installer.

The installer creates the wiki tree, copies the scripts and skills, builds a
`.venv`, installs the dependencies, writes `wiki-kit.json`, adds a section to
`CLAUDE.md`, and runs the self-test.

### 5. Report what actually happened

Read the self-test output. If any check says FAIL, say so plainly and go to
section C - do not report success.

On success, tell them three things:
1. **Restart Claude Code** in this project so the new skills are picked up.
2. Try it: `/wiki-ingest <a URL they care about>`.
3. Then: `/wiki-query <a question about it>`.

### 6. Offer the first real ingest

The kit is worth nothing empty. Offer to ingest one source they actually care
about right now, so the first page exists before they close the session.

---

## B. Add a category later

Re-running the installer is safe and idempotent: existing pages, index entries
and log entries are never touched. New category sections are appended to
`index.md`.

```bash
python wiki-kit/install.py --categories "knowledge,learning,research,projects,people" --yes
```

Pass the **full** list, existing categories included - not just the new one.

---

## C. Verify or repair

```bash
python wiki-kit/install.py --verify-only
```

Read the checks and match the failure:

| Check that failed | What it means | Fix |
|---|---|---|
| dependencies importable | The virtual environment is missing or empty | Re-run the installer without `--verify-only` |
| wiki structure + config | `wiki/`, `index.md` or `log.md` is missing | Re-run the installer |
| web scraper: HTML to markdown | `html2text` or `beautifulsoup4` is broken | Reinstall dependencies |
| pdf converter | `pymupdf` failed to install | Reinstall dependencies; on old Linux it may need a newer pip |
| live fetch (`--network`) | No internet, or the site blocked the request | Not an install problem |

**"The script runs but Python says a module is missing."** The wrong interpreter
was used. Every script must run with the `python` value from `wiki-kit.json`,
not a bare `python`.

**"The slash commands do not exist."** Claude Code reads `.claude/` at startup.
Restart the session.

**Dry run** shows the plan without writing anything:

```bash
python wiki-kit/install.py --dry-run
```

---

## Rules

- Ask about categories before installing, never after. Renaming a shelf once it
  holds pages is real work.
- One installer run. If it fails, diagnose from its output - do not re-run it
  repeatedly hoping for a different result.
- Report the self-test result exactly as it came back. A wiki that is quietly
  half-installed fails later, in the middle of something that mattered.
- Do not hand-create the wiki folders yourself. The installer also writes the
  config and the index that everything else depends on.
