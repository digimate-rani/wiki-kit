---
name: wiki
description: Agent-maintained wiki (second brain) for this project. Routes to the right workflow - query existing knowledge, ingest a new source (URL, PDF, note), batch-ingest an inbox, delete a page, or health-check the wiki. Load whenever the user asks what the project knows about something, asks to save/remember/document a source, or mentions the wiki.
---

# Wiki

A wiki is knowledge that survives between sessions. Pages are written by the
agent, indexed in one file, and read selectively - never all at once.

## Environment

Everything you need is in `wiki-kit.json` at the project root. Read it once per
session, before running any script:

```json
{ "python": "<the interpreter to use>",
  "wiki_root": "wiki",
  "scripts_dir": "scripts/wiki",
  "categories": ["knowledge", "learning", "..."] }
```

Always run the scripts with the `python` value from that file. The project's
system Python usually does not have the dependencies installed.

Below, `wiki/` means the `wiki_root` value. If the project renamed it, substitute.

### When `python` is `null`

The kit was installed without Python, deliberately. Pages, queries, notes,
linting and deleting all work. The two capture scripts cannot run - do not
attempt them with a bare `python`, which turns a known limitation into a
confusing traceback.

**That null records what was true at install time, not what is true now.** The
user may have installed Python since, for this or for anything else. Check
before you tell them something is unavailable:

```bash
py -3 --version        # Windows
python3 --version      # macOS / Linux
```

- **Python is there now** - say so, and offer to switch the scripts on. It is one
  command and it keeps every existing page: `python wiki-kit/install.py --yes`.
  Then continue with whatever they actually asked for.
- **Still missing** - do not stop at "I can't". Say what you can do instead (see
  the fallback in `/wiki-ingest`), and offer `/wiki-setup`, which walks through
  installing Python step by step.

Once the install is finished, `python` in `wiki-kit.json` holds a real path and
none of this applies.

## Intent routing

| The user is asking to | Load this workflow |
|-----------------------|--------------------|
| Answer a question, use what we know, "what do we know about X", "check the wiki" | `.claude/commands/wiki-query.md` |
| Add a URL, a PDF, a note or a brief to the wiki | `.claude/commands/wiki-ingest.md` |
| Process everything waiting in `wiki/inbox/` | `.claude/commands/wiki-ingest-batch.md` |
| Remove a page | `.claude/commands/wiki-delete.md` |
| Health-check: orphans, stale claims, gaps | `.claude/commands/wiki-lint.md` |
| Add a category, re-verify, or fix the install | `.claude/skills/wiki-setup/SKILL.md` |

## The three rules that keep this working

1. **`wiki/index.md` is read first, always.** It is the map. Nothing else is
   read until the index says it is relevant.
2. **Maximum 3-5 pages per task.** If more seem necessary, synthesize what you
   have and ask which direction to go deeper. A wiki that gets read whole is
   just an expensive folder.
3. **Every write touches three files**: the page, `index.md`, and `log.md`.
   A page nobody indexed is a page nobody will ever find.

## Load discipline

- Load only the one workflow that matches. Never all of them.
- If the intent is genuinely ambiguous, ask one short question first.
- Mirror the user's language when talking to them. Wiki pages themselves follow
  whatever language the source is in.
