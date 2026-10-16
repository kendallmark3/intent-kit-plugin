# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This repository is the Intent Kit Claude Code plugin: marketplace `kendall-intent-kit`, plugin `intent-kit`, in `plugins/intent-kit/`. Keep it small. `DESIGN.md` has the promotion rule: add a capability only when it's reusable across projects and stable.

- Commands:
  - `claude plugin validate ./plugins/intent-kit --strict` and `claude plugin validate . --strict`
  - `python3 -m unittest discover -s tests -v`: the secret-guard tests
  - `claude --plugin-dir ./plugins/intent-kit`: try the plugin without installing
- **How the skills connect:** `intent-creator` writes `intents/<slug>.md`, and `execute-intent` fills its `## Delta` and `## Evidence` sections. For multi-file changes, `execute-intent` calls `check-plan` (forked, read-only). A file is an intent only if it has `## Goal` and `## Success Criteria`. Any other file is source material and is never modified.
- **The secret-guard hook:** `hooks/hooks.json` runs `scripts/run-python.sh` → `scripts/secret_guard.py pre|stop`.
  - Never call bare `python`.
  - `pre` mode blocks with exit code 2 and the reason on stderr.
  - `stop` mode blocks once, then only warns (`stop_hook_active`).
- **Release:**
  1. Bump `version` in `plugins/intent-kit/.claude-plugin/plugin.json`.
  2. Commit and push.
  3. `claude plugin tag plugins/intent-kit -m "intent-kit v%s" --push`.
