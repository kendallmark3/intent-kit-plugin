# Design Notes

Intent Kit combines the two starters that scored highest against Intent-Driven Engineering in a side-by-side review:

- **kendallmark3/intent-driven-starter:** the intent pillars, minimum sufficient architecture, capability fit, context contracts, and a small plugin footprint.
- **nathanchase/claude-code-starter:** ideas only, rewritten here: a reuse-first ladder, checking a plan against the code in a forked context, a read-only investigator, and a measurable finish line with bail-out conditions.

## Kept
- Repo-aware source of truth before editing (`start`).
- The four intent pillars, written to a persistent `intent.md` so execution and review can check against it (`intent-creator`).
- Smallest safe delta, written into the intent, with a reuse-first ladder (`execute-intent`).
- Plan checked against the code before multi-file changes (`check-plan`, forked and read-only).
- Evidence table per success criterion; a test counts only after it has been seen failing (`execute-intent`).
- Explicit stop and bail-out conditions.
- Subagents only for isolation: `investigator`, `architecture-reviewer`, `intent-normalizer`, all read-only.
- Context contracts: intent, constraints, state, evidence; no raw history across boundaries.
- One deterministic hook: the secret guard.

## Fixed from intent-driven-starter v1
- The hook called `python`, which macOS does not ship, so it exited 127 (non-blocking) and never ran. It now goes through `run-python.sh`, which finds `python3` / `python` / `py` and tells the user if none exists.
- It printed its reason to stdout on exit 2, which Claude does not see. Reasons now go to stderr (PreToolUse) or the Stop hook's JSON `reason`.
- It only scanned at Stop, after the secret was written. It now blocks at PreToolUse, with Stop as a backstop.
- It missed new untracked files and JSON-style `"api_key": "…"` values. Both are covered.
- A Stop block could repeat forever. It now blocks once, then only warns.

## Left out on purpose
- Domain-specific guidance (the location-story skill stays in intent-driven-starter).
- Ticket-system integrations, PR/commit automation, browser automation, formatting hooks, and MCP servers.
- Multi-agent teams, worker pools, review-cycle machinery.

These are useful in some projects, but they are not universal parts of Intent-Driven Engineering.

## Promotion rule
Do not add a capability because one project used it. Promote it only when multiple projects need the same reusable behavior and the abstraction is stable.
