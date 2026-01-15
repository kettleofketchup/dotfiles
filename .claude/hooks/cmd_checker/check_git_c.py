#!/usr/bin/env python3
"""
Check for git -C patterns that should use cd && git instead.

Using 'git -C <path>' bypasses permission patterns since wildcards
don't work in the middle of patterns. Instead, use 'cd <path> && git <cmd>'
which properly matches existing git permission rules.
"""

import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import block_command

# Pattern to match git -C commands
GIT_C_PATTERN = re.compile(r'^git\s+-C\s+(\S+)\s+(\S+.*)?$')


def check(command: str) -> None:
    """Check command and block if it uses git -C."""
    match = GIT_C_PATTERN.match(command.strip())
    if match:
        path = match.group(1)
        git_cmd = match.group(2) or ""

        # Build the suggested alternative
        if git_cmd:
            suggestion = f"cd {path} && git {git_cmd}"
        else:
            suggestion = f"cd {path} && git <command>"

        lines = [
            "",
            "Suggested alternative:",
            f"  {suggestion}",
            "",
            "Why: Permission patterns like 'Bash(git log:*)' don't match",
            "'git -C <path> log' because wildcards only work at the end.",
            "Using 'cd <path> && git <cmd>' properly matches git permissions.",
        ]

        block_command(
            title="git -C pattern detected",
            pattern_name="git -C <path>",
            command=command,
            problem="git -C bypasses permission patterns (wildcards don't work mid-pattern)",
            solution="Use 'cd <path> && git <command>' instead",
            tool_name="Bash",
            extra_lines=lines
        )


if __name__ == "__main__":
    try:
        data = json.loads(sys.stdin.read())
        command = data.get("tool_input", {}).get("command", "")
        if command:
            check(command)
    except SystemExit:
        raise  # Re-raise sys.exit()
    except Exception:
        pass
    sys.exit(0)
