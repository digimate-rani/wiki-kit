---
description: Delete a wiki page and clean up the index and log. Simple mode - removes the file and its index entry only.
---

# /wiki-delete

<when_to_use>
- "Delete this wiki page", "remove this from the wiki", "this page is wrong"
- A page was created by mistake or has been superseded
</when_to_use>

<steps>

## 1. Identify the target

Accept a path (`wiki/learning/some-page.md`) or a title ("Some Page").
If it is ambiguous, read `wiki/index.md`, show the matching entries, and ask
which one.

## 2. Read `wiki/index.md`

Mandatory. Find the exact line pointing at the page and note its section.

## 3. Confirm - always

> "I'll delete `wiki/learning/some-page.md` and remove its index entry.
> The file is gone permanently. Confirm?"

Wait for an explicit yes. Deletion is not reversible from here.

## 4. Delete the file

## 5. Remove its line from `wiki/index.md`

That one line only. No reformatting, no reordering, no tidying while you are in
there.

## 6. Append `wiki/log.md`

```
## [YYYY-MM-DD] delete | <page title>

File removed: wiki/<category>/<slug>.md
Reason: <what the user said, or "quality" if they said nothing>
Note: cross-references in other pages were NOT cleaned (simple mode).
```

## 7. Confirm

> "Done. Deleted `<path>`, index updated. Links to it from other pages were not
> removed - run `/wiki-lint` if you want to find them."

</steps>

<rules>
- Always confirm before deleting. Always.
- Simple mode only: delete the file, clean the index, write the log. Nothing else.
- Do not edit other pages to strip cross-links - that is a lint job, and doing it
  silently here hides what changed.
- Do not delete the source file in `wiki/sources/` - the page was the mistake,
  the capture may still be useful.
- The log entry is mandatory. A deletion with no record is the one thing nobody
  can reconstruct later.
</rules>
