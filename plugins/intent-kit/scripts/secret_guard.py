#!/usr/bin/env python3
"""intent-kit secret guard. Standard library only.

Modes (hook input JSON arrives on stdin):
  pre   PreToolUse on Write/Edit/MultiEdit. Blocks the write (exit 2, reason on
        stderr for Claude) when the new content contains a credential, unless the
        target file is git-ignored.
  stop  Stop. Scans added lines in the git diff and new untracked files. Asks
        Claude once to remove what it finds; on the retry it only warns the user,
        so it can never trap the session in a loop.

A line containing "intent-kit: allow-secret" is never flagged (for test fixtures).
Any internal error fails open: the session is never blocked by a guard bug.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ALLOW_MARKER = "intent-kit: allow-secret"
MAX_FILE_BYTES = 1_000_000

PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY(?: BLOCK)?-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI API key", re.compile(r"\bsk-(?!ant-)(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}")),
    ("Stripe live key", re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{20,}")),
    (
        "hard-coded secret",
        re.compile(
            r"(?i)(?:api[_-]?key|secret|access[_-]?token|auth[_-]?token|password|passwd)"
            r"[\"']?\s*[:=]\s*[\"']([^\"'\s]{12,})[\"']"
        ),
    ),
]

# Obvious placeholders are not secrets.
PLACEHOLDER = re.compile(
    r"(?i)example|placeholder|changeme|change_me|your[_-]|dummy|redacted|<[^>]*>|\$\{|\{\{|x{6,}|\*{4,}"
)


def scan_text(text: str) -> list[tuple[int, str]]:
    """Return (line_number, kind) for each credential-looking line."""
    hits = []
    for number, line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in line:
            continue
        for kind, rx in PATTERNS:
            match = rx.search(line)
            if match and not PLACEHOLDER.search(match.group(0)):
                hits.append((number, kind))
                break
    return hits


def git(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10)


def is_git_ignored(path: str, cwd: str) -> bool:
    try:
        return git(["check-ignore", "-q", path], cwd).returncode == 0
    except Exception:
        return False


def pre(payload: dict) -> int:
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    path = tool_input.get("file_path", "")
    parts = [tool_input.get("content"), tool_input.get("new_string")]
    parts += [edit.get("new_string") for edit in tool_input.get("edits") or [] if isinstance(edit, dict)]
    text = "\n".join(p for p in parts if isinstance(p, str))

    hits = scan_text(text)
    if not hits or (path and is_git_ignored(path, cwd)):
        return 0

    found = ", ".join(sorted({kind for _, kind in hits}))
    sys.stderr.write(
        f"intent-kit secret guard blocked this write to {path or 'the file'}: possible {found}.\n"
        "Read credentials from environment variables or a secret store instead. "
        f"If this is a deliberate test fixture, add the comment `{ALLOW_MARKER}` on that line.\n"
    )
    return 2


def changed_text(cwd: str) -> dict[str, str]:
    """Added lines per file from the staged and unstaged diff, plus new untracked files."""
    files: dict[str, list[str]] = {}
    for args in (["diff", "--cached"], ["diff"]):
        result = git([*args, "--unified=0", "--no-ext-diff", "--no-color"], cwd)
        if result.returncode != 0:
            continue
        current = None
        for line in result.stdout.splitlines():
            if line.startswith("+++ "):
                current = line[6:] if line.startswith("+++ b/") else None
            elif current and line.startswith("+"):
                files.setdefault(current, []).append(line[1:])

    untracked = git(["ls-files", "--others", "--exclude-standard", "-z"], cwd)
    if untracked.returncode == 0:
        for rel in filter(None, untracked.stdout.split("\0")):
            full = os.path.join(cwd, rel)
            try:
                if os.path.getsize(full) > MAX_FILE_BYTES:
                    continue
                with open(full, "rb") as handle:
                    data = handle.read()
            except OSError:
                continue
            if b"\0" in data:
                continue
            files.setdefault(rel, []).append(data.decode("utf-8", errors="ignore"))

    return {path: "\n".join(lines) for path, lines in files.items()}


def stop(payload: dict) -> int:
    cwd = payload.get("cwd") or os.getcwd()
    try:
        if git(["rev-parse", "--is-inside-work-tree"], cwd).returncode != 0:
            return 0
    except Exception:
        return 0

    found = []
    for path, text in changed_text(cwd).items():
        kinds = sorted({kind for _, kind in scan_text(text)})
        if kinds:
            found.append(f"{path} ({', '.join(kinds)})")
    if not found:
        return 0

    message = (
        "intent-kit secret guard: possible credentials in uncommitted changes: "
        + "; ".join(found)
        + ". Move them to environment variables or a secret store before committing."
    )
    if payload.get("stop_hook_active"):
        # Already asked once this turn: warn the user, let Claude stop.
        print(json.dumps({"systemMessage": message}))
    else:
        print(json.dumps({"decision": "block", "reason": message + f" If one is a deliberate test fixture, add `{ALLOW_MARKER}` on that line."}))
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if mode == "pre":
            return pre(payload)
        if mode == "stop":
            return stop(payload)
        return 0
    except Exception as error:  # fail open, but say so
        print(json.dumps({"systemMessage": f"intent-kit secret guard skipped: {error}"}))
        return 0


if __name__ == "__main__":
    sys.exit(main())
