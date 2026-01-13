#!/usr/bin/env python3
"""
Check for multi-command patterns that should be run separately.

EXCEPTIONS (allowed):
- cd <path> && <single command> (directory context)
- Commands ending with echo (showing results)
- Single commands (obviously)
"""

import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import strip_cd_prefix

# Multi-command split pattern
MULTI_COMMAND_PATTERN = re.compile(r'\s*(?:&&|\|\||;)\s*')


def split_commands(command: str) -> list[str]:
    """Split a bash command into individual commands."""
    commands = []
    lines = command.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        line = re.sub(r'\s*\\$', '', line)
        parts = MULTI_COMMAND_PATTERN.split(line)
        for part in parts:
            part = part.strip()
            if part:
                commands.append(part)

    return commands


def is_exception(command: str, commands: list[str]) -> bool:
    """Check if the multi-command qualifies for an exception."""
    # Allow echo at end of chain (for showing results)
    if len(commands) >= 2:
        last_cmd = commands[-1].strip()
        if last_cmd.startswith('echo ') or last_cmd == 'echo':
            return True
    return False


def check(command: str) -> None:
    """Check command and block if it contains multiple commands."""
    # Strip cd prefix (cd /path && cmd is allowed)
    command_without_cd = strip_cd_prefix(command)
    commands = split_commands(command_without_cd)

    # Single command is always allowed
    if len(commands) <= 1:
        return

    # Check for exceptions
    if is_exception(command, commands):
        return

    # Block multi-command
    lines = [
        "=" * 60,
        "BLOCKED: Multiple commands detected",
        "=" * 60,
        "",
        "This command contains multiple chained commands that should be",
        "run separately for proper permission management.",
        "",
        "Commands to run individually:",
        "",
    ]

    for i, cmd in enumerate(commands, 1):
        lines.append(f"  {i}. {cmd}")

    lines.extend([
        "",
        "Why this matters:",
        "  - Each command can be individually added to the permission allow list",
        "  - Failures are easier to identify and debug",
        "  - Permission prompts are clearer for each operation",
        "",
        "Exceptions allowed:",
        "  - cd <path> && <single command>",
        "  - Commands ending with echo (showing results)",
    ])

    print('\n'.join(lines), file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    try:
        data = json.loads(sys.stdin.read())
        command = data.get("tool_input", {}).get("command", "")
        if command:
            check(command)
    except SystemExit:
        raise
    except Exception:
        pass
    sys.exit(0)
