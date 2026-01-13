#!/usr/bin/env python3
"""Check for in-place edit patterns that should use the Edit tool."""

import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import check_patterns, block_command

# Edit patterns - should use Edit tool
EDIT_PATTERNS = [
    (re.compile(r'^sed\s+.*-i'),
     "sed -i",
     "Use the Edit tool for in-place file modifications",
     "Edit"),

    (re.compile(r'^sed\s+-i'),
     "sed -i",
     "Use the Edit tool for in-place file modifications",
     "Edit"),

    (re.compile(r'^awk\s+.*-i\s*inplace'),
     "awk -i inplace",
     "Use the Edit tool for in-place file modifications",
     "Edit"),
]


def check(command: str) -> None:
    """Check command and block if it matches edit patterns."""
    match = check_patterns(command, EDIT_PATTERNS)
    if match:
        pattern_name, suggestion, correct_tool = match
        block_command(
            title="In-place edit pattern detected",
            pattern_name=pattern_name,
            command=command,
            problem="Using Bash for in-place edits bypasses change tracking",
            solution=suggestion,
            tool_name=correct_tool,
            extra_lines=[
                "It provides proper change tracking and",
                "permission management for file modifications."
            ]
        )


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
