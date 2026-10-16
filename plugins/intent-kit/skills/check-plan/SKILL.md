---
name: check-plan
description: Check an intent's Delta (or any plan file) against the actual code before implementation — verify every file and assumption, find missed callers, and cut anything the success criteria do not need. Use before implementing a multi-file or shared-code change.
argument-hint: "[path to intent or plan file]"
context: fork
allowed-tools: Read Grep Glob
---

# Check Plan

Review the plan in `$ARGUMENTS` against the code as it is now. Without an argument, use the intent being executed in this conversation; if there is none, use the only file in `intents/` (or a root `intent.md`); if several exist, ask which. Read-only: report, do not edit.

## Verify
For every item in the plan's Delta:
- **Files to change:** the file exists, and the names, structures, and line references the plan relies on match the code.
- **Files intentionally unchanged:** grep for the symbols being changed; confirm nothing in these files depends on them.
- **Shared code:** list every caller of each function, type, or export the plan changes. A caller the plan does not mention is a finding.
- **Patterns cited:** the cited precedent exists and actually works the way the plan says.
- **Assumptions and invariants:** trace the code path; a claim you cannot confirm from the code is a finding.

## Cut
For each planned change, ask in order: does a success criterion need it? does the repository already have it? does the standard library or an installed dependency do it? Anything that fails the first question is scope creep — recommend removing it.

## Report
```markdown
## Plan check: <READY | FIX FIRST>

### Findings
- [blocker|should-fix|note] <finding> — evidence: `path:line`

### Missed callers / files
- `path:line` — <why it is affected>

### Cut
- <planned change> — <why it is not needed>
```

Verdict is FIX FIRST only if at least one blocker exists. Keep the report short; every finding carries a `path:line`.
