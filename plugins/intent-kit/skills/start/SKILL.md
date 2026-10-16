---
name: start
description: Start work in an existing or unfamiliar repository with the repo-aware Intent-Driven Engineering posture. Use at the beginning of a feature, bug fix, refactor, or onboarding session, before proposing changes.
---

# Start — Repo-Aware Onboarding

Understand the repository before proposing architecture or editing code.

## Read first
1. Read repository guidance: `CLAUDE.md`, `AGENTS.md`, README files, any `intent.md` / spec / feature file, and the package manifests.
2. Establish the implemented state from code and tests. Roadmap and spec prose are claims, not state.
3. Find the real validation path: the test, typecheck, lint, and build commands the repository actually uses.
4. Find the smallest set of files that implement the area in question, and the existing patterns nearby.

For a broad or unfamiliar area, delegate the reading to the `investigator` agent and keep only its report.

## Report back, briefly
- What already works.
- What must change.
- What must not change.
- How the change will be validated (exact commands).
- Unknowns that block correct work, if any.

Do not ask the user to restate what the repository or conversation already says.

## Match the effort to the work
| The work is… | Do this |
|---|---|
| An obvious, small change (rename, one-line fix) | Make it, run the relevant check, stop. |
| A feature, fix, or refactor with real acceptance criteria | `intent-creator` (if no intent exists), then `execute-intent`. |
| A change that adds an external system, persistence/auth topology, workflow engine, MCP server, or shared service | Ask the `architecture-reviewer` agent first. |

## Architecture posture
- Goal-oriented by default. Procedural control only where ordering, gates, side effects, retries, or failure cost require it.
- Skill = reusable know-how. Hook = deterministic rule that must not be bypassed. Tool = external action. MCP = governed access to an external system. Subagent = specialization, isolation, or useful parallel work.
- Reuse what the repository already has before adding frameworks, services, agents, or dependencies.
