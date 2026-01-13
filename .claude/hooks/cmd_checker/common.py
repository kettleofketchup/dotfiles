"""
Common utilities for cmd_checker modules.

Provides shared functionality:
- Input parsing from Claude Code
- Pattern checking helpers
- Output formatting for blocked commands
- Logging utilities
"""

import json
import sys
import re
from typing import Optional

# Log file for debugging
LOG_PATH = "/tmp/bash-hook-debug.log"


def log(message: str) -> None:
    """Append a message to the debug log."""
    with open(LOG_PATH, "a") as f:
        f.write(f"{message}\n")


def parse_input() -> Optional[dict]:
    """
    Parse JSON input from Claude Code stdin.

    Returns:
        dict with tool_name, tool_input, etc. or None if not a Bash tool call
    """
    try:
        raw_input = sys.stdin.read()
        input_data = json.loads(raw_input)

        tool_name = input_data.get("tool_name", "")
        if tool_name != "Bash":
            return None

        return input_data
    except json.JSONDecodeError as e:
        log(f"JSON decode error: {e}")
        return None


def get_command(input_data: dict) -> str:
    """Extract the command string from parsed input."""
    tool_input = input_data.get("tool_input", {})
    return tool_input.get("command", "")


def get_description(input_data: dict) -> str:
    """Extract the description from parsed input."""
    tool_input = input_data.get("tool_input", {})
    return tool_input.get("description", "")


def check_patterns(command: str, patterns: list) -> Optional[tuple[str, str, str]]:
    """
    Check command against a list of patterns.

    Args:
        command: The bash command to check
        patterns: List of (regex, name, suggestion, tool) tuples

    Returns:
        (pattern_name, suggestion, tool_name) if matched, None otherwise
    """
    for pattern, name, suggestion, tool in patterns:
        if pattern.search(command):
            return (name, suggestion, tool)
    return None


def block_command(
    title: str,
    pattern_name: str,
    command: str,
    problem: str,
    solution: str,
    tool_name: str,
    extra_lines: Optional[list[str]] = None
) -> None:
    """
    Print a formatted block message and exit with code 2.

    Args:
        title: The block reason (e.g., "File write pattern detected")
        pattern_name: Name of the matched pattern
        command: The command that was blocked
        problem: Description of why this is a problem
        solution: What to do instead
        tool_name: The correct tool to use
        extra_lines: Optional additional lines to include
    """
    cmd_display = command[:200] + ('...' if len(command) > 200 else '')

    lines = [
        "=" * 60,
        f"BLOCKED: {title}",
        "=" * 60,
        "",
        f"Pattern:  {pattern_name}",
        f"Command:  {cmd_display}",
        "",
        f"Problem:  {problem}",
        f"Solution: {solution}",
        "",
        f"The {tool_name} tool is the correct way to perform this operation.",
    ]

    if extra_lines:
        lines.extend(extra_lines)

    log(f"BLOCKED: {title} - {pattern_name}")
    print('\n'.join(lines), file=sys.stderr)
    sys.exit(2)


def allow_command() -> None:
    """Allow the command to proceed."""
    sys.exit(0)


def skip_hook() -> None:
    """Skip this hook (not applicable)."""
    sys.exit(0)


# Pattern for cd prefix: cd <path> &&
CD_PREFIX_PATTERN = re.compile(r'^cd\s+(?:"[^"]*"|\'[^\']*\'|\S+)\s*&&\s*')


def strip_cd_prefix(command: str) -> str:
    """Strip leading 'cd <path> &&' from a command."""
    return CD_PREFIX_PATTERN.sub('', command.strip())
