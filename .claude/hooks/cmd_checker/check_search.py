#!/usr/bin/env python3
"""
Check for search patterns that should use Grep/Glob tools.

EXCEPTIONS (allowed):
- Single grep/rg command (not chained) - useful for quick context
- grep -c or grep | wc (counting matches)
- grep | head/tail (getting subset)
"""

import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import check_patterns, block_command

# Search patterns - should use Grep/Glob tools
SEARCH_PATTERNS = [
    (re.compile(r'^grep\s+'),
     "grep",
     "Use the Grep tool for content searching",
     "Grep"),

    (re.compile(r'^rg\s+'),
     "rg (ripgrep)",
     "Use the Grep tool for content searching",
     "Grep"),

    (re.compile(r'^find\s+.*-name\s+'),
     "find -name",
     "Use the Glob tool for finding files by pattern",
     "Glob"),

    (re.compile(r'^find\s+.*-type\s+'),
     "find -type",
     "Use the Glob tool for finding files",
     "Glob"),
]

# Patterns that indicate allowed exceptions
EXCEPTION_PATTERNS = [
    re.compile(r'^(?:grep|rg)\s+.*\|\s*wc\b'),      # grep | wc
    re.compile(r'^(?:grep|rg)\s+.*-c\b'),           # grep -c
    re.compile(r'^(?:grep|rg)\s+-c\b'),             # grep -c at start
    re.compile(r'^(?:grep|rg)\s+.*\|\s*(?:head|tail)\b'),  # grep | head/tail
]


def is_exception(command: str) -> bool:
    """Check if the command qualifies for an exception."""
    # Check explicit exception patterns
    for pattern in EXCEPTION_PATTERNS:
        if pattern.search(command):
            return True

    # Allow single grep/rg commands (not chained with && or ||)
    if re.match(r'^(?:grep|rg)\s+', command):
        if '&&' not in command and '||' not in command:
            return True

    return False


def check(command: str, input_data: dict = None) -> None:
    """Check command and block if it matches search patterns."""
    # Check for exceptions first
    if is_exception(command):
        return

    match = check_patterns(command, SEARCH_PATTERNS)
    if match:
        pattern_name, suggestion, correct_tool = match
        block_command(
            title="Search pattern detected",
            pattern_name=pattern_name,
            command=command,
            problem="Using Bash for searching is less integrated",
            solution=suggestion,
            tool_name=correct_tool,
            extra_lines=[
                "It is optimized for searching and provides",
                "better integration with Claude Code.",
                "",
                "Note: Single grep/rg commands ARE allowed.",
            ]
        )


if __name__ == "__main__":
    try:
        data = json.loads(sys.stdin.read())
        command = data.get("tool_input", {}).get("command", "")
        if command:
            check(command, data)
    except SystemExit:
        raise
    except Exception:
        pass
    sys.exit(0)
