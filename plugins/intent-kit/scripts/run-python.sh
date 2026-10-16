#!/bin/sh
# Run a Python 3 script with whichever interpreter this machine has (python3, python, or the Windows py launcher).
# If none exists, tell the user the guard is off instead of failing silently, and never block the session.
for py in python3 python py; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
    exec "$py" "$@"
  fi
done
printf '%s\n' '{"systemMessage": "intent-kit: Python 3 was not found, so the secret guard is not running. Install Python 3 to enable it."}'
exit 0
