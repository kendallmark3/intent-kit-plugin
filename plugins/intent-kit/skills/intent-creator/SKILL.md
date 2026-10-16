---
name: intent-creator
description: Create or refine an intent file using the Intent Creator standard (Goal, Inputs/Context, Outputs, Success Criteria, plus constraints and stop). Turns any rough input — a Jira story, ticket, notes, or a file the user dropped in — into an intent. Use when the user asks to create an intent, turn something into an intent, or says "intent creator".
argument-hint: "[goal, ticket text, or path to a story/notes file or existing intent]"
---

# Intent Creator

Produce an implementation-ready intent: strong enough for autonomous, repo-aware execution, with no more constraint than the work needs.

## Input
Work out what `$ARGUMENTS` is:
- **A path to an existing intent:** a file in `intents/`, or any file that already has the template's `## Goal` and `## Success Criteria` sections. Refine it in place.
- **A path to anything else** (story, ticket export, notes, a hand-written `intent.md`): this is **source material**. Read it and **never modify, rename, or delete it**. Create a new intent from it, and list the source path under Inputs / Context.
- **Text:** use it as source material.
- **Empty:** use what the user said in the conversation. If that gives no goal, look for a file the user just added outside `intents/` (for example untracked in `git status`). If exactly one candidate exists, use it as source material and say which file you used; if several exist, ask which one.

## Steps
1. Read the repository enough to ground the intent (guidance files, the affected area, the real validation commands). Do not invent repository facts.
2. Fill the four required pillars. Add the optional sections only when they change what gets built.
3. Make every success criterion checkable: a command, an observable behavior, or a file state someone can verify.
4. Mark genuinely unknown required information as `UNKNOWN:` and ask about it only if it blocks correct work.
5. Write the intent to `intents/<slug>.md`, where `<slug>` is a short kebab-case name for the goal (for example `intents/add-name-flag.md`). Use another path only if the user names one or the repository already keeps intents elsewhere.
   - **Never overwrite a different intent.** If the target file exists and describes a different goal, choose a new slug.
   - When refining an existing intent, edit it in place and keep what is already right.
   - Never write the intent over the source material file.
6. Tell the user the path, so `execute-intent <path>` can pick it up.

## Template
```markdown
# Intent: <short title>

## Goal
<The outcome, in one paragraph. Why it matters.>

## Inputs / Context
- <Current state, with file references>
- <Relevant data, contracts, tickets, prior decisions>

## Outputs
- <What will exist or behave differently when done>

## Success Criteria
- [ ] <Checkable criterion> — check: `<command or observation>`
- [ ] <Checkable criterion> — check: `<command or observation>`

## Constraints            <!-- optional -->
- <Must / must not>

## Out of Scope           <!-- optional -->
- <Adjacent work deliberately excluded>

## Delta                  <!-- filled by execute-intent -->

## Evidence               <!-- filled by execute-intent -->

## Stop
Done when every success criterion is shown satisfied in Evidence and the repository's checks pass.
Bail out and report if: <conditions, e.g. needs a new external dependency, needs another repository, verification cannot go green>.
```

## Posture
- Minimum sufficient architecture. Smallest safe change. Reuse repository patterns.
- Goal-oriented by default; add procedure only where ordering, gates, side effects, or failure cost justify it.
- Delta mode is fine: when extending an existing intent, add only what changes.
- Do not add architecture, polish, or adjacent features the user did not ask for.
