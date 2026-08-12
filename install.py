#!/usr/bin/env python3
"""
wiki-kit installer - sets up an agent-maintained wiki in any Claude Code project.

What it does, in order:
  1. Works out which project it is installing into
  2. Adds the ignore rules, so the environment it is about to build never
     reaches a repository
  3. Creates the wiki folder tree (categories are yours to choose)
  4. Copies the scripts into <project>/scripts/wiki/
  5. Copies the skills and slash commands into <project>/.claude/
  6. Creates a Python virtual environment and installs the dependencies
  7. Writes wiki-kit.json so every part can find the others
  8. Adds a short wiki section to the project's CLAUDE.md
  9. Runs the self-test and reports the result

Typical use:
    python install.py                                   # install into the parent project
    python install.py --categories knowledge,learning   # pick the folders up front
    python install.py --list-categories                 # print the catalog as JSON
    python install.py --verify-only                     # just re-run the checks
    python install.py --dry-run                         # show the plan, change nothing

Requires Python 3.9+. Everything here is standard library.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import venv
from datetime import date
from pathlib import Path

KIT = Path(__file__).resolve().parent
VERSION = "1.0.0"

CATEGORY_CATALOG = {
    "knowledge": "API docs, references and structured facts the agent builds against",
    "learning": "Tools, concepts and techniques you are learning",
    "research": "Investigations, comparisons, market and competitor findings",
    "projects": "One page per project: decisions, current state, gotchas",
    "operations": "Things you ran: launches, campaigns, workshops, incidents",
    "people": "People, companies and brands you deal with",
    "data": "Datasets, metrics and numbers, each with its provenance",
    "documentation": "How your own systems work, written for future you",
}
DEFAULT_CATEGORIES = ["knowledge", "learning", "research", "projects"]

SOURCE_KINDS = ["web", "pdf", "local"]

CLAUDE_MD_START = "<!-- wiki-kit:start -->"
CLAUDE_MD_END = "<!-- wiki-kit:end -->"

actions = []


def say(msg=""):
    print(msg, flush=True)


def step(msg):
    say(f"\n=== {msg}")


def did(msg):
    actions.append(msg)
    say(f"  + {msg}")


def skipped(msg):
    say(f"  . {msg}")


# ---------------------------------------------------------------- target root

def resolve_target(explicit) -> Path:
    """
    The project being installed into. If the kit sits inside the project (the
    usual case, cloned as <project>/wiki-kit), the parent is the target.
    """
    if explicit:
        return Path(explicit).expanduser().resolve()

    cwd = Path.cwd().resolve()
    if cwd == KIT:
        return KIT.parent
    if KIT.parent == cwd:
        return cwd
    return cwd


def looks_like_project(path: Path) -> bool:
    markers = [".git", ".claude", "CLAUDE.md", "package.json", "pyproject.toml"]
    return any((path / m).exists() for m in markers)


# ----------------------------------------------------------------- gitignore

GITIGNORE_RULES = [".venv/", "venv/", "__pycache__/", "*.pyc", "wiki-kit/"]


def ensure_gitignore(target: Path, dry: bool):
    """
    Runs before anything else is created, and the venv is the reason why.

    A few steps from now this installer builds .venv/ - thousands of files and
    hundreds of megabytes that must never reach a repository. Someone who runs
    `git add .` before noticing has a genuinely hard mess to undo, and it is not
    a mess a beginner can be expected to clean up. The rules go in first, so the
    window where that can happen never opens.

    An existing .gitignore is never rewritten. Only the missing lines are added.
    """
    step("Git ignore rules")
    path = target / ".gitignore"

    old = path.read_text(encoding="utf-8") if path.is_file() else ""
    # "/.venv/", ".venv" and ".venv/" all mean the same thing here.
    covered = {ln.strip().strip("/") for ln in old.splitlines()
               if ln.strip() and not ln.lstrip().startswith(("#", "!"))}

    missing = [rule for rule in GITIGNORE_RULES if rule.strip("/") not in covered]
    if not missing:
        skipped(".gitignore already covers the environment and the caches")
        return

    block = ("# wiki-kit - the environment and the caches are rebuilt, never committed\n"
             + "\n".join(missing) + "\n")
    if not dry:
        text = (old.rstrip() + "\n\n" + block) if old.strip() else block
        path.write_text(text, encoding="utf-8")
    did(f".gitignore {'updated' if old.strip() else 'created'}: {', '.join(missing)}")


# ------------------------------------------------------------------ wiki tree

def index_template(categories, project_name) -> str:
    lines = [
        "# Wiki Index",
        "",
        "> Master catalog - one entry per page, added on every ingest.",
        "> Format: `[Page Title](category/page.md) - one line summary *(Sources: N, Updated: YYYY-MM-DD)*`",
        "",
        f"> Project: {project_name}",
        "",
        "---",
        "",
    ]
    for cat in categories:
        lines += [
            f"## {cat.replace('-', ' ').title()}",
            f"*{CATEGORY_CATALOG.get(cat, 'Custom category')}*",
            "",
            "<!-- entries are added here as pages are created -->",
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


LOG_TEMPLATE = """# Wiki Log

> Append-only history. Every ingest, delete and lint gets one entry.
> Newest entries at the bottom.

---
"""

INBOX_README = """# Inbox

Drop anything here that should become wiki knowledge later:

- `.md` notes and briefs
- `.pdf` files (they get converted first)
- `urls.txt` with one URL per line

Then run `/wiki-ingest-batch` in Claude Code. Processed files move to
`inbox/done/` so nothing is ingested twice.
"""


def build_wiki(target: Path, wiki_root: str, categories, dry: bool):
    step("Wiki folders")
    wiki = target / wiki_root
    project_name = target.name

    for cat in categories:
        d = wiki / cat
        if d.is_dir():
            skipped(f"{wiki_root}/{cat}/ already exists")
        elif not dry:
            d.mkdir(parents=True, exist_ok=True)
            (d / ".gitkeep").touch()
            did(f"{wiki_root}/{cat}/")
        else:
            did(f"{wiki_root}/{cat}/  (dry run)")

    for kind in SOURCE_KINDS:
        d = wiki / "sources" / kind
        if not d.is_dir():
            if not dry:
                d.mkdir(parents=True, exist_ok=True)
                (d / ".gitkeep").touch()
            did(f"{wiki_root}/sources/{kind}/")

    inbox = wiki / "inbox"
    if not inbox.is_dir():
        if not dry:
            (inbox / "done").mkdir(parents=True, exist_ok=True)
            (inbox / "README.md").write_text(INBOX_README, encoding="utf-8")
        did(f"{wiki_root}/inbox/")

    index = wiki / "index.md"
    if index.is_file():
        skipped("index.md exists - leaving your entries alone")
        if not dry:
            add_missing_sections(index, categories)
    else:
        if not dry:
            index.write_text(index_template(categories, project_name), encoding="utf-8")
        did(f"{wiki_root}/index.md")

    log = wiki / "log.md"
    if log.is_file():
        skipped("log.md exists")
    else:
        if not dry:
            log.write_text(LOG_TEMPLATE, encoding="utf-8")
        did(f"{wiki_root}/log.md")


def add_missing_sections(index: Path, categories):
    """Re-running with new categories must add sections without touching entries."""
    text = index.read_text(encoding="utf-8")
    added = []
    for cat in categories:
        heading = f"## {cat.replace('-', ' ').title()}"
        if heading not in text:
            text = text.rstrip() + (
                f"\n\n{heading}\n*{CATEGORY_CATALOG.get(cat, 'Custom category')}*\n\n"
                "<!-- entries are added here as pages are created -->\n\n---\n"
            )
            added.append(cat)
    if added:
        index.write_text(text, encoding="utf-8")
        did(f"index.md: added sections for {', '.join(added)}")


# --------------------------------------------------------------- file copying

def copy_scripts(target: Path, scripts_dir: str, dry: bool):
    step("Scripts")
    dest = target / scripts_dir
    if not dry:
        dest.mkdir(parents=True, exist_ok=True)
    for src in sorted((KIT / "scripts").glob("*.py")):
        if not dry:
            shutil.copy2(src, dest / src.name)
        did(f"{scripts_dir}/{src.name}")


def copy_agent_files(target: Path, dry: bool):
    step("Skills and slash commands")
    skills_src = KIT / ".claude" / "skills"
    cmds_src = KIT / ".claude" / "commands"
    for src in (skills_src, cmds_src):
        if not src.is_dir():
            raise SystemExit(
                f"  ! missing from the kit: {src}\n"
                "    The kit is incomplete - re-clone it."
            )

    skills_dst = target / ".claude" / "skills"
    cmds_dst = target / ".claude" / "commands"
    if not dry:
        skills_dst.mkdir(parents=True, exist_ok=True)
        cmds_dst.mkdir(parents=True, exist_ok=True)

    for skill_dir in sorted(skills_src.iterdir()):
        if not skill_dir.is_dir():
            continue
        dst = skills_dst / skill_dir.name
        if not dry:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(skill_dir, dst)
        did(f".claude/skills/{skill_dir.name}/")

    for cmd in sorted(cmds_src.glob("*.md")):
        if not dry:
            shutil.copy2(cmd, cmds_dst / cmd.name)
        did(f".claude/commands/{cmd.name}")


# ------------------------------------------------------------------ python env

def venv_python(vdir: Path) -> Path:
    return vdir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_python(target: Path, use_venv: bool, with_playwright: bool, dry: bool):
    step("Python environment")
    if not use_venv:
        skipped(f"using the current interpreter: {sys.executable}")
        py = Path(sys.executable)
    else:
        vdir = target / ".venv"
        py = venv_python(vdir)
        if py.is_file():
            skipped(f".venv already exists ({py})")
        elif dry:
            did(".venv/  (dry run)")
            return py, False
        else:
            say("  creating .venv (this takes a few seconds)...")
            venv.EnvBuilder(with_pip=True, clear=False).create(vdir)
            did(".venv/")

    if dry:
        return py, False

    reqs = [line.strip() for line in
            (KIT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]
    if with_playwright:
        reqs.append("playwright>=1.40")

    say(f"  installing: {', '.join(r.split('>')[0] for r in reqs)}")
    proc = subprocess.run(
        [str(py), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", *reqs],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        say("  ! dependency install failed:")
        say("    " + (proc.stderr or proc.stdout).strip().splitlines()[-1][:300])
        return py, False
    did("dependencies installed")

    if with_playwright:
        say("  downloading the Chromium browser for Playwright (large, one time)...")
        pw = subprocess.run([str(py), "-m", "playwright", "install", "chromium"],
                            capture_output=True, text=True)
        if pw.returncode == 0:
            did("playwright chromium")
        else:
            say("  ! playwright browser download failed - the scraper still works "
                "for normal pages")

    return py, True


# ---------------------------------------------------------------- config file

def write_config(target: Path, py: Path, wiki_root, scripts_dir, categories,
                 with_playwright, dry: bool):
    step("Config")
    try:
        rel_py = str(py.resolve().relative_to(target.resolve())).replace("\\", "/")
    except ValueError:
        rel_py = None

    cfg = {
        "wiki_kit_version": VERSION,
        "installed": date.today().isoformat(),
        "python": str(py),
        "python_relative": rel_py,
        "wiki_root": wiki_root,
        "scripts_dir": scripts_dir,
        "categories": categories,
        "playwright": with_playwright,
    }
    if not dry:
        (target / "wiki-kit.json").write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    did("wiki-kit.json")
    return cfg


# ------------------------------------------------------------------ CLAUDE.md

def claude_md_block(wiki_root, scripts_dir, categories, py_hint):
    cats = ", ".join(f"`{wiki_root}/{c}/`" for c in categories)
    return f"""{CLAUDE_MD_START}
## Wiki - the project's second brain

This project has an agent-maintained wiki at `{wiki_root}/`. It is the memory
that survives between sessions. Treat it as a real source, not decoration.

- **Before answering from general knowledge**, read `{wiki_root}/index.md` and check
  whether the wiki already covers the topic. Cite the pages you used.
- **Never read the whole wiki.** Read `index.md`, then only the 3-5 pages it points to.
- **Categories:** {cats}
- **Adding knowledge:** run `/wiki-ingest` with a URL, a PDF path or a note.
  PDFs are converted to markdown first, then ingested.
- **Tools:** `{py_hint} {scripts_dir}/scrape_web.py` and
  `{py_hint} {scripts_dir}/convert_pdf_to_md.py`. Paths and the exact Python to
  use are in `wiki-kit.json`.

Slash commands: `/wiki-query`, `/wiki-ingest`, `/wiki-ingest-batch`,
`/wiki-lint`, `/wiki-delete`, `/wiki-setup`.
{CLAUDE_MD_END}"""


def patch_claude_md(target: Path, block: str, dry: bool):
    step("CLAUDE.md")
    path = target / "CLAUDE.md"
    if not path.is_file():
        if not dry:
            path.write_text(f"# Project Instructions\n\n{block}\n", encoding="utf-8")
        did("CLAUDE.md created with the wiki section")
        return

    text = path.read_text(encoding="utf-8")
    if CLAUDE_MD_START in text and CLAUDE_MD_END in text:
        head = text.split(CLAUDE_MD_START)[0]
        tail = text.split(CLAUDE_MD_END, 1)[1]
        if not dry:
            path.write_text(head + block + tail, encoding="utf-8")
        did("CLAUDE.md wiki section refreshed")
    else:
        if not dry:
            path.write_text(text.rstrip() + "\n\n" + block + "\n", encoding="utf-8")
        did("CLAUDE.md wiki section appended")


# ---------------------------------------------------------------- self-test

def run_selftest(target: Path, py: Path, scripts_dir: str, network: bool) -> bool:
    step("Self-test")
    script = target / scripts_dir / "selftest.py"
    if not script.is_file():
        say("  ! selftest.py missing - install did not complete")
        return False
    cmd = [str(py), str(script)] + (["--network"] if network else [])
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(target))
    say(proc.stdout.rstrip())
    if proc.returncode != 0:
        say(proc.stderr.rstrip()[:1500])
    return proc.returncode == 0


# ---------------------------------------------------------------- categories

def choose_categories(arg_value, assume_yes, known=None) -> list:
    if arg_value:
        picked = [c.strip().lower().replace(" ", "-")
                  for c in arg_value.split(",") if c.strip()]
        return picked or DEFAULT_CATEGORIES

    # Already installed here - keep the shelves the user picked last time.
    # This matters most when finishing an install that was started without
    # Python: without it, --yes would quietly add the four defaults on top of
    # whatever they actually chose.
    if known:
        return list(known)

    if assume_yes or not sys.stdin.isatty():
        return DEFAULT_CATEGORIES

    say("\nWhich wiki folders do you want? Pick by number, comma separated.")
    keys = list(CATEGORY_CATALOG)
    for i, key in enumerate(keys, 1):
        mark = "*" if key in DEFAULT_CATEGORIES else " "
        say(f"  {i}. {mark} {key.ljust(14)} {CATEGORY_CATALOG[key]}")
    say("  (* = default. Enter for the defaults, or type your own names.)")
    raw = input("> ").strip()
    if not raw:
        return DEFAULT_CATEGORIES

    picked = []
    for part in raw.split(","):
        part = part.strip().lower()
        if not part:
            continue
        if part.isdigit() and 1 <= int(part) <= len(keys):
            picked.append(keys[int(part) - 1])
        else:
            picked.append(part.replace(" ", "-"))
    return picked or DEFAULT_CATEGORIES


# --------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Install the wiki kit into a Claude Code project")
    ap.add_argument("--target", help="Project folder (default: the folder containing this kit)")
    ap.add_argument("--categories", help="Comma separated wiki folders to create")
    ap.add_argument("--wiki-root", help="Wiki folder name (default: wiki)")
    ap.add_argument("--scripts-dir", help="Where the scripts go (default: scripts/wiki)")
    ap.add_argument("--yes", "-y", action="store_true", help="Accept defaults, ask nothing")
    ap.add_argument("--with-playwright", action="store_true",
                    help="Also install Playwright, for JavaScript-heavy sites")
    ap.add_argument("--no-venv", action="store_true",
                    help="Use the current Python instead of creating .venv")
    ap.add_argument("--network", action="store_true", help="Include a live fetch in the self-test")
    ap.add_argument("--verify-only", action="store_true", help="Only run the self-test")
    ap.add_argument("--dry-run", action="store_true", help="Show the plan, change nothing")
    ap.add_argument("--list-categories", action="store_true",
                    help="Print the category catalog as JSON and exit")
    args = ap.parse_args()

    if args.list_categories:
        print(json.dumps({"catalog": CATEGORY_CATALOG, "defaults": DEFAULT_CATEGORIES},
                         indent=2))
        return 0

    target = resolve_target(args.target)
    say(f"wiki-kit {VERSION}")
    say(f"Installing into: {target}")
    if args.dry_run:
        say("DRY RUN - nothing will be written")

    # An earlier install here decides the defaults for this one.
    existing = {}
    cfg_path = target / "wiki-kit.json"
    if cfg_path.is_file():
        try:
            existing = json.loads(cfg_path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            existing = {}

    wiki_root = args.wiki_root or existing.get("wiki_root") or "wiki"
    scripts_dir = args.scripts_dir or existing.get("scripts_dir") or "scripts/wiki"

    if args.verify_only:
        if not existing:
            say("No wiki-kit.json found - the kit is not installed here.")
            return 1
        if not existing.get("python"):
            # A no-Python install: the pages and the reading commands work, the
            # capture scripts cannot. There is no environment to test yet.
            say("\nThis project was set up without Python.")
            say("  Reading, writing and querying pages works.")
            say("  Capturing web pages and PDFs does not - those need Python.")
            say("")
            say("Finish the install once Python is available:")
            say('  python wiki-kit/install.py --yes')
            return 1
        ok = run_selftest(target, Path(existing["python"]), scripts_dir, args.network)
        return 0 if ok else 1

    if target == KIT:
        say("\nRefusing to install into the kit folder itself.")
        say("Run this from your project, or pass --target <project folder>.")
        return 1

    if not looks_like_project(target):
        say(f"\nThat does not look like a project folder:")
        say(f"  {target}")
        say("  Nothing there marks a project: no .git, .claude, CLAUDE.md, "
            "package.json or pyproject.toml.")
        say("")
        say("The kit installs INTO a project. It is not a standalone tool, and it")
        say("cannot install into its own folder.")
        say("")
        say("Two ways to fix it:")
        say("  1. Put the kit inside your project, so it sits at")
        say("     <your-project>/wiki-kit/, then run it again.")
        say("  2. Name the project explicitly:")
        say('     python install.py --target "<path to your project>"')

        # --yes means "accept the defaults", not "skip the safety check". An agent
        # running unattended must stop here and ask the user where this should go.
        if args.yes or not sys.stdin.isatty():
            say("")
            say("Stopping. Nothing was written.")
            return 1
        if input("\nInstall into it anyway? [y/N] ").strip().lower() not in ("y", "yes"):
            say("Stopping. Nothing was written.")
            return 1

    categories = choose_categories(args.categories, args.yes,
                                   existing.get("categories"))
    say(f"\nCategories: {', '.join(categories)}")

    ensure_gitignore(target, args.dry_run)
    build_wiki(target, wiki_root, categories, args.dry_run)
    copy_scripts(target, scripts_dir, args.dry_run)
    copy_agent_files(target, args.dry_run)
    py, deps_ok = ensure_python(target, not args.no_venv, args.with_playwright, args.dry_run)

    py_hint = f".venv/{'Scripts/python' if os.name == 'nt' else 'bin/python'}" \
        if not args.no_venv else "python"
    write_config(target, py, wiki_root, scripts_dir, categories,
                 args.with_playwright, args.dry_run)
    patch_claude_md(target, claude_md_block(wiki_root, scripts_dir,
                                            categories, py_hint), args.dry_run)

    if args.dry_run:
        say(f"\nDry run complete. {len(actions)} actions would run.")
        return 0

    ok = deps_ok and run_selftest(target, py, scripts_dir, args.network)

    step("Result")
    if ok:
        say("  Wiki kit installed and verified.")
        say("")
        say("  Next steps:")
        say("    1. Restart Claude Code in this project so it picks up the new skills.")
        say("    2. Try:  /wiki-ingest https://some-page-you-care-about.com")
        say("    3. Then: /wiki-query what do we know about ...")
    else:
        say("  Installed, but the self-test did not pass. See the output above.")
        say(f"  Re-run the checks with:  python wiki-kit/install.py --verify-only")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
