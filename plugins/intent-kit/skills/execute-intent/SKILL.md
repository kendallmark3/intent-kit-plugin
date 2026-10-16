---
name: execute-intent
description: Execute an intent file with the understand → delta → check plan → implement → prove → stop discipline. Use for repo-aware implementation of a feature, fix, or refactor that has an intent or clear acceptance criteria.
argument-hint: "[path to intent file]"
---

# Execute Intent

The repository and the intent are the source of truth.

Find the intent file, in this order:
1. `$ARGUMENTS`, if given.
2. The intent created or named earlier in this conversation.
3. The only intent in `intents/` (or a root `intent.md`) with unchecked success criteria.
4. If several qualify, list them and ask which one. If none exist, use the intent in the conversation, or run `intent-creator` first.

A file counts as an intent only if it has `## Goal` and `## Success Criteria` sections. Anything else (a story, notes, a hand-written `intent.md`) is source material: run `intent-creator` on it first, and leave the original file untouched.

Work in that one file only; other intents belong to other work.

## 1. Understand
- Read the intent and the repository guidance.
- If a required pillar (Goal, Inputs/Context, Outputs, Success Criteria) is missing or a success criterion is not checkable, fix only that gap — with `intent-creator` or one question to the user — then continue.
- Determine current state from code and tests. For a broad or unfamiliar surface, use the `investigator` agent and keep only its report.
- Preserve existing public behavior unless the intent changes it.

## 2. Delta
Write the smallest delta that satisfies the success criteria into the intent's `## Delta` section:
- files to change, and what changes in each;
- files intentionally unchanged that a reader might expect to change;
- the existing pattern each change follows (`file:line`);
- new dependency only if unavoidable, with the reason.

Climb this ladder for each change and stop at the first rung that holds:
1. Does it need to exist at all? If not, skip it and say so in one line.
2. Does the repository already have it? Reuse it.
3. Does the language's standard library or the platform do it?
4. Does an already-installed dependency do it?
5. Only then: the least code that works.

Fix root causes: before changing a shared function, find its callers. Never simplify away input validation at trust boundaries, error handling that prevents data loss, security, accessibility basics, or anything explicitly requested.

## 3. Check the plan
If the delta touches more than one file, or touches shared code, run the `check-plan` skill on the intent file and fold its findings into the delta before writing code. Skip it for a single, local change.

## 4. Implement
- Follow the repository's patterns and standards.
- Keep reasoning responsible for interpretation; keep deterministic code responsible for state, validation, security boundaries, persistence, identifiers, and irreversible actions.
- Do not fabricate external facts or tool results. Do not bypass hooks or validation.
- When delegating to a subagent, pass only intent, constraints, relevant state, and the expected output shape — not raw history or credentials.

## 5. Prove
Run the repository's real checks (tests, typecheck, lint, build, or a focused runtime check). Record evidence in the intent's `## Evidence` section, one row per success criterion:

```markdown
| Criterion | Check run | Result |
|---|---|---|
| <criterion> | `<command>` or <observation> | <exit code / key output / file:line> |
```

- A criterion without a row is not done. When its row passes, tick its checkbox in `## Success Criteria`.
- A new test counts only after it has been seen failing for the right reason, then passing. Report both runs.
- If a check fails, fix the code. Changing an assertion to get green is the user's decision.

## 6. Stop
Stop when every success criterion has passing evidence and the repository's checks pass. Report the evidence table and nothing more.

The finish line is one condition: *every success criterion shown satisfied in Evidence, the repository's checks pass, and no files outside the Delta changed.* For long hands-off runs the user can hand this condition to `/goal` with a turn limit.

Bail out and report instead of pushing on if:
- the only viable path needs a new external dependency or service the intent did not allow;
- the change needs another repository or system the user has not authorized;
- the same check fails twice for the same reason after a genuine fix attempt;
- the intent turns out to contradict the code or itself.

Do not promote a local solution into a shared service, framework, agent, MCP server, or workflow unless repeated use or a hard requirement justifies it.
