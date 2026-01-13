#!/usr/bin/env python3
"""Test script for cmd_checker modules."""

import subprocess
import json
import sys
import os

CMD_CHECKER_DIR = os.path.dirname(os.path.abspath(__file__))
HOOKS_DIR = os.path.dirname(CMD_CHECKER_DIR)


def test_module(module, command, should_block, description):
    """Test a single check module."""
    module_path = os.path.join(CMD_CHECKER_DIR, module)
    r = subprocess.run(
        ["python3", module_path],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
        capture_output=True, text=True
    )
    blocked = r.returncode == 2
    status = "PASS" if blocked == should_block else "FAIL"
    return status, description, blocked


def test_full_checker(command, should_block, description):
    """Test the full cmd_checker module."""
    r = subprocess.run(
        ["python3", "-m", "cmd_checker"],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
        capture_output=True, text=True,
        cwd=HOOKS_DIR
    )
    blocked = r.returncode == 2
    status = "PASS" if blocked == should_block else "FAIL"
    return status, description, blocked


def main():
    print("Testing cmd_checker modules...\n")

    # Individual module tests
    module_tests = [
        ("check_search.py", "grep pattern file.txt", False, "single grep (allowed)"),
        ("check_search.py", "rg pattern src/", False, "single rg (allowed)"),
        ("check_write.py", "echo hello > file.txt", True, "echo redirect (blocked)"),
        ("check_write.py", "echo hello", False, "echo no redirect (allowed)"),
        ("check_read.py", "cat README.md", True, "cat file (blocked)"),
        ("check_read.py", "git status", False, "non-read (allowed)"),
        ("check_edit.py", "sed -i 's/a/b/' file", True, "sed -i (blocked)"),
        ("check_multi_command.py", "cmd1 && cmd2", True, "&& chain (blocked)"),
        ("check_multi_command.py", "cd /tmp && ls", False, "cd && cmd (allowed)"),
        ("check_multi_command.py", "git status", False, "single cmd (allowed)"),
    ]

    passed = failed = 0
    print("Individual module tests:")
    for module, cmd, should_block, desc in module_tests:
        status, description, blocked = test_module(module, cmd, should_block, desc)
        result = "blocked" if blocked else "allowed"
        print(f"  [{status}] {module}: {desc} -> {result}")
        if status == "PASS":
            passed += 1
        else:
            failed += 1

    # Full cmd_checker tests
    full_tests = [
        ("git status", False, "git status (allowed)"),
        ("ls -la", False, "ls (allowed)"),
        ("echo hello > file.txt", True, "write pattern (blocked)"),
        ("grep pattern file", False, "single grep (allowed)"),
        ("cmd1 && cmd2", True, "multi-cmd (blocked)"),
    ]

    print("\nFull cmd_checker tests:")
    for cmd, should_block, desc in full_tests:
        status, description, blocked = test_full_checker(cmd, should_block, desc)
        result = "blocked" if blocked else "allowed"
        print(f"  [{status}] {desc} -> {result}")
        if status == "PASS":
            passed += 1
        else:
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
