#!/usr/bin/env python3
"""
cmd_checker - Modular bash command validator for Claude Code.

Runs all check modules IN PARALLEL using subprocess for speed.
Each module can block a command by returning exit code 2.
If any check blocks, the command is blocked.
"""

import sys
import os
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# Directory containing check modules
CMD_CHECKER_DIR = os.path.dirname(os.path.abspath(__file__))

# Log file
LOG_PATH = "/tmp/bash-hook-debug.log"

# Check modules to run (in parallel)
CHECK_MODULES = [
    "check_write.py",
    "check_read.py",
    "check_search.py",
    "check_edit.py",
    "check_multi_command.py",
    "check_git_c.py",
]


def log(message: str) -> None:
    """Append to debug log."""
    with open(LOG_PATH, "a") as f:
        f.write(f"{message}\n")


def run_check(module: str, input_json: str) -> tuple[str, int, str]:
    """
    Run a single check module.

    Returns: (module_name, exit_code, stderr_output)
    """
    module_path = os.path.join(CMD_CHECKER_DIR, module)
    try:
        result = subprocess.run(
            ["python3", module_path],
            input=input_json,
            capture_output=True,
            text=True,
            timeout=4  # Per-module timeout
        )
        return (module, result.returncode, result.stderr)
    except subprocess.TimeoutExpired:
        return (module, 0, "")  # Timeout = allow (fail open)
    except Exception as e:
        log(f"Error running {module}: {e}")
        return (module, 0, "")  # Error = allow (fail open)


def main():
    log("=" * 40)
    log("cmd_checker invoked (parallel mode)")

    # Read input once
    try:
        raw_input = sys.stdin.read()
        input_data = json.loads(raw_input)
    except json.JSONDecodeError as e:
        log(f"JSON decode error: {e}")
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    log(f"Checking: {command[:100]}")

    # Run all checks in parallel
    with ThreadPoolExecutor(max_workers=len(CHECK_MODULES)) as executor:
        futures = {
            executor.submit(run_check, module, raw_input): module
            for module in CHECK_MODULES
        }

        for future in as_completed(futures):
            module, exit_code, stderr = future.result()

            # If any check blocks (exit 2), block the command
            if exit_code == 2:
                log(f"BLOCKED by {module}")
                # Print the stderr from the blocking module
                if stderr:
                    print(stderr, file=sys.stderr, end='')
                sys.exit(2)

    # All checks passed
    log(f"ALLOWED: {command[:100]}")
    sys.exit(0)


if __name__ == "__main__":
    main()
