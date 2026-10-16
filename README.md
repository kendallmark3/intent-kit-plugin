# Intent Kit for Claude Code

A Claude Code plugin for Intent-Driven Engineering: understand the repository, state the intent, make the smallest safe change, prove it against the success criteria, and stop.

It installs no MCP server, workflow engine, database, framework, or cloud dependency.

## Install

From any terminal:

```bash
claude plugin marketplace add kendallmark3/intent-kit-plugin
claude plugin install intent-kit@kendall-intent-kit --scope user
```

Or inside Claude Code:

```text
/plugin marketplace add kendallmark3/intent-kit-plugin
/plugin install intent-kit@kendall-intent-kit
```

Choose **User** scope so it is available in every project. If Claude Code asks you to reload, run `/reload-plugins`.

To install from a local copy of this folder instead, replace `kendallmark3/intent-kit-plugin` with the folder path.

To try it without installing:

```bash
claude --plugin-dir ./plugins/intent-kit
```

Update later with `claude plugin update intent-kit@kendall-intent-kit`.

## Use

```text
/intent-kit:start                      understand the repository before changing it
/intent-kit:intent-creator <goal>      write intents/<slug>.md with the four pillars
/intent-kit:execute-intent [path]      build it: delta → check plan → implement → prove → stop
/intent-kit:check-plan [path]          check a plan against the code (execute-intent runs it when needed)
```

Each piece of work gets its own intent file under `intents/`, so parallel features never overwrite each other. Commit them with the code. They record what was asked, what changed, and the evidence that it works.

The sequence:

```text
repository state
      ↓
intent: goal, inputs/context, outputs, success criteria
      ↓
smallest safe delta  →  checked against the code
      ↓
implementation
      ↓
evidence for every success criterion (repository's own checks)
      ↓
STOP
```

## What is included

### Skills
- **`start`:** reads the repository first: guidance files, implemented state, the real validation commands, the smallest affected surface. Matches the effort to the work.
- **`intent-creator`:** writes `intents/<slug>.md` (never overwriting a different intent) with Goal, Inputs/Context, Outputs, checkable Success Criteria, optional Constraints / Out of Scope, and Stop / bail-out conditions.
- **`execute-intent`:** writes the delta into the intent, applies a reuse-first ladder (need it? → already here? → standard library? → installed dependency? → least code), runs `check-plan` for multi-file changes, implements, records an evidence table per success criterion, and stops or bails out on stated conditions.
- **`check-plan`:** runs in a forked, read-only context. It verifies every file, caller, and assumption in the delta against the code, flags scope creep, and returns READY or FIX FIRST with `path:line` evidence.

### Agents
- **`investigator`:** read-only. Answers one question about the repository with a short report and `path:line` evidence instead of file dumps.
- **`architecture-reviewer`:** read-only. Used only for real architecture expansion: a new external system, persistence/auth topology, workflow engine, trust boundary, shared service, or MCP server.
- **`intent-normalizer`:** turns a bounded piece of free text into a compact intent contract without pulling in unrelated context.

### Hook: secret guard
- **Before every Write / Edit / MultiEdit:** blocks content containing a credential (private keys; AWS, GitHub, Anthropic, OpenAI, Slack, Google and Stripe keys; hard-coded `password` / `api_key` / `secret` / `token` values, including JSON style). Claude is told why and what to do. Writes to git-ignored files such as `.env` are allowed.
- **When Claude finishes a turn:** scans added lines in the git diff and new untracked files, and asks Claude once to remove anything found. After that it only warns, so it cannot loop.
- **Allow marker:** a line containing `intent-kit: allow-secret` is never flagged, for deliberate test fixtures.
- **Requirements:** needs Python 3 (`python3`, `python`, or `py`), standard library only. Without Python it tells you the guard is off instead of failing silently.

A Claude Code hook does not replace server-side validation or a CI secret scanner.

## Verify

```bash
claude plugin validate ./plugins/intent-kit --strict
claude plugin validate . --strict
python3 -m unittest discover -s tests -v
```

## License

MIT. See [LICENSE](LICENSE).

## Version 1 posture

Keep it small. Add a capability only after it proves reusable across projects and its shape is stable. Keep project-specific capability in the project.
