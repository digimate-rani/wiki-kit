---
description: Answer a question or produce work using the wiki. Index first, then only the pages that matter - never the whole wiki.
---

# /wiki-query

<when_to_use>
- The user asks something the wiki may already cover
- The user asks for content or a decision where accumulated knowledge is relevant
- "What do we know about X", "check the wiki", "use what we have"
- Before answering from general knowledge on any topic the project has worked on
</when_to_use>

<token_rule>
**Never read the whole wiki. Read the index, then read only what the index points to.**
Three to five pages per query, maximum. If more seem necessary, answer with what
you have and ask which direction to go deeper.
</token_rule>

<steps>

## 1. Read `wiki/index.md` - and nothing else yet

One small file that lists everything that exists and where it lives.
(`wiki/` = the `wiki_root` value in `wiki-kit.json`.)

## 2. Pick the relevant pages, maximum 3-5

Choose by the one-line descriptions. Prioritize:
- Direct match - the page is about exactly this
- Entity pages - for a person, company or product
- Synthesis pages - for strategic or comparative context

If nothing matches: say so. "This isn't in the wiki yet - want me to ingest a
source on it?" is a better answer than a confident guess.

## 3. Read those pages fully

Only those. Do not open a page "just in case" - that is how a cheap query turns
into an expensive one.

## 4. Answer

Use what you read. Cite inline: `→ [Page Title](wiki/category/page.md)`.

Separate the two kinds of knowledge explicitly. If part of the answer comes from
the wiki and part from general knowledge, say which is which. The whole value of
a wiki is that its claims are traceable.

Do not pad with caveats. If the wiki answers it, answer. If it answers half, say
which half is missing.

## 5. Offer to file the synthesis, if it was real work

If the answer required non-obvious synthesis across pages and would be useful
again:

> "Worth saving this as its own wiki page?"

If yes: write it, update `index.md`, append `log.md`.

## 6. Log - only if a page was filed

```
## [YYYY-MM-DD] query | <question>

Pages consulted: <list>
Filed as: <path>
Key insight: <one line>
```

No page filed, no log entry.

</steps>

<rules>
- `index.md` is the only guaranteed read. Everything else is conditional on it.
- 3-5 pages maximum. More than that means the question is too broad - narrow it.
- Never present general knowledge as wiki knowledge. Mark the boundary.
- If the wiki does not have it, say that. An honest gap is a research lead; a
  confident guess is a future wrong decision.
- Cite the pages. The links are half the value.
</rules>
