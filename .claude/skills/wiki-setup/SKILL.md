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

### 0. Check that Python exists

`install.py` is a Python script. If there is no interpreter, every later step
fails in a way that looks like a broken kit. Check first:

```bash
py -3 --version        # Windows
python3 --version      # macOS / Linux
```

- Prints **3.9 or newer** - continue to step 1.
- Prints an older version, prints nothing, or errors - go to **section D**. It
  is a fork, not a dead end: the user chooses between installing the wiki now
  without Python, or installing Python first. Both paths end in a working wiki.

On Windows, `python --version` printing nothing or "Python was not found" means
you hit the Microsoft Store stub, not a real interpreter. Treat it as missing
and check section D.

Do not silently skip this. A missing interpreter is the one failure the
installer cannot report on, because it never gets to run.

### 1. Find the kit and the project

The kit is usually cloned as `<project>/wiki-kit/`. Confirm `install.py` exists
before doing anything else.

**Then work out which folder is the project, and say it out loud before you
install anything.** The installer assumes the folder holding the kit is the
project. That assumption is wrong in one common case: the user cloned the kit
on its own, so the kit *is* the top folder and its parent is some unrelated
folder full of other projects. Installing there scatters a wiki tree into it.

Check it: does the intended project folder contain `.git`, `.claude`,
`CLAUDE.md`, `package.json` or `pyproject.toml`? If none of them are there, do
not guess. Tell the user which folder you are about to install into and ask
whether that is really their project. The installer stops on its own in this
case, but you should catch it first - it is a confusing failure to hit blind.

If the project is somewhere else, pass `--target "<project folder>"`.

If the kit was cloned on its own with no project around it, there is nothing to
install into. The kit cannot install into its own folder. Ask the user which
project the wiki belongs to, then move the kit inside it, or pass `--target`.

Check whether it is already installed. If `wiki-kit.json` exists at the project
root, this is not a fresh install - read it and route on what it says:

| `wiki-kit.json` says | Go to |
|---|---|
| `"python": null` | **section E** - the install was finished except for Python |
| a real `python` path, and they want a new category | section B |
| a real `python` path, and something is broken | section C |

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

If `--verify-only` reports *"This project was set up without Python"*, nothing is
broken. That is the deferred install described in section D1, working as
intended - go to section E.

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

## D. Python is missing

### First, confirm it really is missing

Run every candidate before concluding anything - a machine often has Python
under a name you did not try:

```bash
py -3 --version        # Windows launcher - the most reliable check
python3 --version
python --version
```

Windows has one specific trap. `python.exe` under
`AppData\Local\Microsoft\WindowsApps` is a stub that opens the Microsoft Store;
it prints "Python was not found" and exits non-zero. If `where.exe python`
returns *only* that path, there is no real Python:

```powershell
where.exe python
```

### Then give the user the choice - do not decide for them

Python is **not** what makes the wiki work. It powers the two capture scripts,
nothing else. Say that plainly before asking anything:

| Works with no Python at all | Needs Python |
|---|---|
| `/wiki-query` - asking the wiki anything | `/wiki-ingest` with a **URL** (the web scraper) |
| `/wiki-lint`, `/wiki-delete` | `/wiki-ingest` with a **PDF** (the converter) |
| `/wiki-ingest` with a note, or a file that is already text or markdown | `/wiki-ingest-batch` over PDFs and URL lists |

Then ask one question, with both answers on the table:

> Python isn't installed on this machine. The wiki itself doesn't need it - you
> can write, read and query pages today. What needs it is capturing web pages
> and PDFs automatically.
>
> 1. **Set the wiki up now, add Python later.** Everything gets installed,
>    capture scripts included, just switched off. Whenever you want them, I walk
>    you through installing Python step by step and turn them on in one command.
> 2. **Install Python first.** A few minutes and a download of about 30 MB, then
>    the full kit in one go.

Never install software on someone's machine without them saying yes to it.

---

### D1. Option 1 - install now, add Python later

`install.py` is itself a Python script, so it cannot run. You create the same
result by hand. Do all of it - a half-built wiki is worse than none.

Ask which categories they want first, exactly as in section A step 2 (read the
catalog out of `install.py`'s `CATEGORY_CATALOG`, since `--list-categories`
needs Python too).

Then produce, in this order:

1. **`.gitignore`** - append the missing rules from `GITIGNORE_RULES`.
2. **Folders** - `wiki/<category>/` for each chosen category,
   `wiki/sources/web/`, `wiki/sources/pdf/`, `wiki/sources/local/`, each with an
   empty `.gitkeep`, plus `wiki/inbox/done/`.
3. **`wiki/index.md`, `wiki/log.md`, `wiki/inbox/README.md`.**
4. **Scripts** - copy `wiki-kit/scripts/*.py` to `scripts/wiki/`. They are copied
   even though they cannot run yet; that is the point of this option.
5. **Skills and commands** - copy `wiki-kit/.claude/skills/*` to
   `.claude/skills/` and `wiki-kit/.claude/commands/*.md` to `.claude/commands/`.
6. **`wiki-kit.json`** - see below.
7. **`CLAUDE.md`** - append the wiki section.

**Do not invent the file contents.** Every template lives in `wiki-kit/install.py`
- read `GITIGNORE_RULES`, `index_template`, `LOG_TEMPLATE`, `INBOX_README` and
`claude_md_block`, and write out exactly what each one would have produced.
Duplicating them from memory is how the two paths drift apart.

`wiki-kit.json` is the one file that differs. `python` is `null`, and that null
is meaningful - it is how everything else knows the capture scripts are not
available yet:

```json
{
  "wiki_kit_version": "1.0.0",
  "installed": "<today, YYYY-MM-DD>",
  "python": null,
  "python_relative": null,
  "wiki_root": "wiki",
  "scripts_dir": "scripts/wiki",
  "categories": ["<the ones they chose>"],
  "playwright": false
}
```

The `CLAUDE.md` section needs one change, and it is the most important line you
will write today. `CLAUDE.md` is read automatically at the start of **every**
session - it is how a session three weeks from now, in a fresh context, finds
out that Python is missing before it tries to scrape something. Replace the
`**Tools:**` bullet with exactly this:

```markdown
- **Capture scripts:** installed but **not active** - this project was set up
  without Python. Writing, reading and querying pages works normally. Adding a
  URL or a PDF does not, until Python is installed. To finish: `/wiki-setup`.
  (`wiki-kit.json` has `"python": null` for the same reason.)
```

Do not leave the original command lines there. A command that cannot work is
worse than no command - it gets tried, it fails, and the failure looks like a
broken kit rather than a deliberate choice the user made.

**Keep the `<!-- wiki-kit:start -->` and `<!-- wiki-kit:end -->` comments around
the block.** They are how the installer finds this section later: when Python
arrives, it replaces everything between them with the normal version, and the
warning above disappears on its own. Lose the markers and the finished install
appends a second wiki section instead of replacing this one, leaving the project
with contradictory instructions.

Finish by telling them, in this order:

1. Restart Claude Code so the commands appear.
2. What works today - querying, notes, and pasting text in by hand.
3. What is waiting - URLs and PDFs.
4. How to finish, whenever they want: say "finish the wiki install" or run
   `/wiki-setup`, and you pick up at section D2.

**Completing it later is one command.** Once Python exists, run the normal
installer - it is idempotent, keeps every page and index entry, reuses the
categories already in `wiki-kit.json`, and fills in the missing environment:

```bash
python wiki-kit/install.py --yes
```

---

### D2. Option 2 - install Python now

**Which version.** Download **3.12.x**. Anything from 3.11 to 3.13 is fine. Two
limits worth respecting:

- **Not the newest release** (3.14 and up). The kit depends on `pymupdf`, and for
  a just-released Python there is often no ready-made package yet - `pip` then
  tries to build it from source, which needs a C compiler the user does not have.
- **Not below 3.9.** Nothing here supports it.

If Python 3.9 or newer is *already* installed, leave it alone. Do not upgrade
someone's Python to satisfy a preference.

#### Windows

`winget` is Microsoft's own installer tool and ships with Windows 11 and Windows
10 (1809 and later), so it is usually present. Check first:

```powershell
winget --version
```

**If winget is there:**

```powershell
winget install --id Python.Python.3.12 -e --source winget --scope user `
  --accept-package-agreements --accept-source-agreements
```

`--scope user` installs into the user's own profile, which avoids the
administrator pop-up you cannot click. If winget rejects that scope, do not
retry without it blindly - that version can raise the pop-up. Hand the command
to the user instead.

**If winget is missing, or it failed** - walk them through it. Do not just paste
a link:

> 1. Open <https://www.python.org/downloads/windows/>
> 2. Under **Python 3.12.x**, click **Windows installer (64-bit)**.
> 3. Open the file you downloaded.
> 4. On the first screen, tick **"Add python.exe to PATH"** at the bottom. This
>    is the step everyone misses, and skipping it is what makes Python
>    "installed but not found".
> 5. Click **Install Now** and wait for it to finish.
> 6. Tell me when it is done.

**PATH is stale after either route.** Your shell inherited its environment when
the session started, so `python` still fails even though Python now exists. Do
not conclude the install failed. Check the absolute path instead:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" --version
```

and run the installer with that same absolute path:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" wiki-kit/install.py --categories "..." --yes
```

That is safe: `install.py` builds `.venv` from whichever interpreter runs it and
writes the resulting absolute path into `wiki-kit.json`, so everything afterwards
finds the right Python regardless of PATH. Tell the user to restart Claude Code
once; after that a bare `python` works normally.

If you cannot find the interpreter at all, ask the user to close and reopen
Claude Code, then check again. A fresh session picks up the new PATH.

#### macOS

```bash
brew --version
brew install python@3.12
```

No Homebrew: **do not install it yourself.** Its installer asks for an
administrator password, and your shell cannot answer a prompt - it will hang or
fail. Walk them through the official installer instead:

> 1. Open <https://www.python.org/downloads/macos/>
> 2. Download **macOS 64-bit universal2 installer** for Python 3.12.x.
> 3. Open it and click through - the defaults are correct.
> 4. Tell me when it is done.

#### Linux

Most package managers need `sudo`, which needs a password you cannot type.
Check whether this machine allows it without one:

```bash
sudo -n true          # exit 0 = passwordless sudo, safe to proceed
```

If yes:

```bash
sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip   # Debian / Ubuntu
sudo dnf install -y python3 python3-pip                                            # Fedora / RHEL
sudo pacman -S --noconfirm python                                                  # Arch
```

If no, give the user the exact line and ask them to run it in their own terminal.

On Debian and Ubuntu, `python3-venv` matters. Without it Python exists but
`python -m venv` fails, and the installer dies half way through building `.venv`
with an error that does not name the real cause.

#### After installing

Re-run the detection commands and read the actual output before continuing. Do
not assume it worked because a command exited quietly. Then go back to section A
step 1 and install normally.

If the install did not work, offer option D1 rather than looping. A wiki they can
use today beats a fourth attempt at a dependency.

---

## E. Finish an install that was made without Python

`wiki-kit.json` has `"python": null`. The wiki is real and in use; the two
capture scripts have never been switched on. You arrive here either because the
user asked to finish, or because they asked for something - a URL, a PDF - that
needs the scripts.

**Check whether Python is already there before saying anything about it.** Weeks
may have passed and they may have installed it for something else entirely.
Nothing is more annoying than being walked through installing what you already
have:

```bash
py -3 --version        # Windows
python3 --version      # macOS / Linux
```

### Python is there

One command. Do not re-ask about categories - the installer reads them from
`wiki-kit.json` and reuses them:

```bash
python wiki-kit/install.py --yes
```

Add `--with-playwright` only if they ask about JavaScript-heavy sites.

It keeps every page, index entry and log line, fills in `.venv`, installs the
dependencies, rewrites `wiki-kit.json` with the real interpreter, refreshes the
`CLAUDE.md` section, and runs the self-test. Report that result exactly as it
came back, as in section A step 5.

Then tell them to restart Claude Code, and **go back to what they originally
asked for.** Finishing the install is not the task; it was in the way of the
task.

### Python is still missing

Go to **section D2** and walk them through it. Two things to keep in mind:

- If they would rather not deal with it now, that is a legitimate answer. Use the
  `/wiki-ingest` fallback so the thing they came for still gets done, and leave
  the install for another day. Do not ask twice in one session.
- Do not treat this as a fresh install. The wiki already exists. Never re-create
  folders, never overwrite `index.md`.

---

## Rules

- Check for Python before anything else. If it is missing, offer both options -
  a wiki without capture scripts is still a wiki, and it is not your call to
  make someone install a language they did not ask for.
- Never run an installer that needs a password or a click. Your shell cannot
  answer either, so hand that command to the user and wait.
- Ask about categories before installing, never after. Renaming a shelf once it
  holds pages is real work.
- One installer run. If it fails, diagnose from its output - do not re-run it
  repeatedly hoping for a different result.
- Report the self-test result exactly as it came back. A wiki that is quietly
  half-installed fails later, in the middle of something that mattered.
- Do not hand-create the wiki folders yourself. The installer also writes the
  config and the index that everything else depends on.
