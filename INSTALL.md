# Instructions for the agent

You are installing the wiki kit into this project.

Read `wiki-kit/.claude/skills/wiki-setup/SKILL.md` and follow **section A**.

**Before anything else, check that Python 3.9+ exists on this machine.** The
installer is a Python script - without an interpreter nothing here runs, and the
failure looks like a broken kit rather than a missing dependency.

```bash
py -3 --version        # Windows
python3 --version      # macOS / Linux
```

If that prints 3.9 or newer, carry on with section A.

If it does not, go to **section D** of the same skill file. Python is only
needed for capturing web pages and PDFs - the wiki itself works without it - so
section D is a choice to put to the user, not a blocker: install the wiki now
and add Python later, or install Python first. Do not decide it for them, and
do not install anything on their machine without a yes.

Ask the user which wiki categories they want **before** running the installer.
Then run it once, and report the self-test result exactly as it came back.
