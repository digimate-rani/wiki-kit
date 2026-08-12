---
description: Install, extend, verify or repair the project wiki. Run this once when setting up, and again whenever you want to add a category or check that everything still works.
---

# /wiki-setup

Load `.claude/skills/wiki-setup/SKILL.md` and follow it.

Pick the right section:

- **Nothing installed yet** (no `wiki-kit.json` at the project root) → section A,
  first-time install. Ask which categories they want before running anything.
- **Adding a category** → section B.
- **Something is broken, or you just want to check** → section C, verify and repair.
- **No Python on this machine** → section D. It is a choice, not a blocker: the
  wiki works without it, only web and PDF capture do not.
- **`wiki-kit.json` says `"python": null`**, or the user says "finish the
  install" → section E. Check whether Python turned up first; if it did, one
  command completes everything and keeps every page.
