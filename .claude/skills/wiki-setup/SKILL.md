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
- Prints an older version, prints nothing, or errors - go to **section D**,
  install Python, then come back here.

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

## D. Python is missing

**Ask before installing anything.** Say what it is, roughly how large, and where
it goes. Installing software on someone's machine is not part of "install the
wiki" unless they agree to it.

### Confirm it is really missing

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

### Windows

`winget` ships with Windows 10 (1809+) and Windows 11. Check, then install:

```powershell
winget --version
winget install --id Python.Python.3.12 -e --source winget --scope user `
  --accept-package-agreements --accept-source-agreements
```

`--scope user` installs under the user's profile and avoids the administrator
prompt. If winget rejects that scope for this package, re-run without it - but
that version may raise a UAC dialog, which you cannot click. If it does, hand
the command to the user to run in their own terminal.

No winget: send them to <https://www.python.org/downloads/> and tell them to
tick **"Add Python to PATH"** in the installer.

**PATH is stale after the install.** Your shell inherited its environment when
the session started, so `python` will still fail even though Python now exists.
Do not conclude the install failed. Verify with the absolute path instead:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" --version
```

and use that same absolute path to run the installer:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" wiki-kit/install.py --categories "..." --yes
```

That is safe: `install.py` builds `.venv` from whichever interpreter runs it and
writes the resulting absolute path into `wiki-kit.json`, so everything
afterwards finds the right Python regardless of PATH. Tell the user to restart
Claude Code once, after which a bare `python` works normally.

### macOS

```bash
brew --version
brew install python@3.12
```

No Homebrew: **do not install it yourself.** Its installer asks for an
administrator password, and your shell cannot answer a prompt - it will hang or
fail. Point the user at <https://www.python.org/downloads/macos/> instead, or
give them the Homebrew command to run themselves.

### Linux

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

If no, print the command and ask the user to run it in their own terminal.

On Debian and Ubuntu, `python3-venv` matters. Without it Python exists but
`python -m venv` fails, and the installer dies half way through building `.venv`
with an error that does not name the real cause.

### After installing

Re-run the detection commands and read the actual output before continuing. Do
not assume the install worked because the command exited quietly.

---

## Rules

- Check for Python before anything else, and never install it without asking.
  Never run an installer that needs a password or a click - your shell cannot
  answer either, so hand that command to the user instead.
- Ask about categories before installing, never after. Renaming a shelf once it
  holds pages is real work.
- One installer run. If it fails, diagnose from its output - do not re-run it
  repeatedly hoping for a different result.
- Report the self-test result exactly as it came back. A wiki that is quietly
  half-installed fails later, in the middle of something that mattered.
- Do not hand-create the wiki folders yourself. The installer also writes the
  config and the index that everything else depends on.
