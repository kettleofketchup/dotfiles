#!/usr/bin/env python3
"""PreToolUse hook: refuse `cd <dir> && <command>` in Bash.

A compound `cd` is worse than it looks in this harness:

* The Bash tool's working directory PERSISTS between calls, so the `cd` is
  redundant — run it once on its own, or pass the directory to the command.
* Chaining it hides the real command from the permission layer, so a compound
  that would otherwise be allow-listed prompts instead.
* A worktree-isolated session refuses compounds it cannot statically prove stay
  inside the worktree, so `cd … && git …` is rejected outright.
* The user's global CLAUDE.md already bans it for git specifically ("Use
  `git -C <path>`. Do NOT `cd` into a directory to run git commands").

Almost every tool takes the directory directly, which is the fix:

    cd react-pages && npm run lint     ->  npm --prefix react-pages run lint
    cd src && grep -rn foo .           ->  grep -rn foo src
    cd repo && git status              ->  git -C repo status
    cd build && make                   ->  make -C build
    cd d && pytest                     ->  pytest d      (or cd d, then pytest)

Escape hatch: put `# allow-cd` anywhere in the command when the chain is
genuinely required (a subshell that must not move the caller's cwd, a tool with
no directory flag).

Wiring (user-global, in dotfiles): a `PreToolUse` hook with matcher `Bash`.
Input is JSON on stdin; a `permissionDecision: "deny"` in hookSpecificOutput
blocks the call and feeds the reason back to Claude.
"""

import json
import re
import sys

# A `cd` whose target is followed by a chain operator. Anchored to the start of a
# command position (line start, or just after ; && || |, or an opening subshell
# paren) so `grep "cd x && y" file` and a bare `cd foo` are both left alone.
PATTERN = re.compile(r"(?:^|[;&|]|\()\s*cd\s+[^\s&;|)]+\s*(?:&&|\|\||;)")

OPT_OUT = "# allow-cd"

REASON = (
    "Compound `cd <dir> && <command>` is blocked. The Bash tool's working "
    "directory persists between calls, so the `cd` is redundant — and chaining "
    "it hides the real command from the permission layer (turning an "
    "allow-listed command into a prompt) and is refused outright in a "
    "worktree-isolated session.\n\n"
    "Run the command against the directory instead:\n"
    "  npm --prefix <dir> run <script>     not  cd <dir> && npm run <script>\n"
    "  git -C <dir> <subcommand>           not  cd <dir> && git <subcommand>\n"
    "  make -C <dir>                       not  cd <dir> && make\n"
    "  grep -rn <pattern> <dir>            not  cd <dir> && grep -rn <pattern> .\n"
    "  <tool> <dir>                        or   an absolute path in the command\n\n"
    "If you genuinely need to move first, issue the bare `cd <dir>` as its own "
    "call — it sticks for later calls. If the chain is truly required (a "
    "subshell that must not move the caller's cwd, a tool with no directory "
    "flag), add `# allow-cd` to the command."
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # Never block on a malformed payload.

    if payload.get("tool_name") != "Bash":
        return 0

    command = (payload.get("tool_input") or {}).get("command") or ""
    if OPT_OUT in command or not PATTERN.search(command):
        return 0

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": REASON,
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    # `--selftest` keeps the pattern honest without a separate test file; the
    # false-positive cases are the ones that actually matter here.
    if "--selftest" in sys.argv:
        blocked = [
            "cd /home/u/proj/react-pages/src && grep -rln foo",
            "cd react-pages && npm run lint",
            "cd foo; ls",
            "ls && cd bar && make",
            "(cd sub && tar cf ../a.tar .)",
            "cd d || true",
        ]
        allowed = [
            "cd /home/u/proj/react-pages",          # bare cd, its own call
            "grep -rn 'cd x && y' src",             # the text inside an argument
            "npm --prefix react-pages run lint",
            "make -C build",
            "echo done && npm test",                # a chain with no cd
            "cd sub && ./run.sh  # allow-cd",       # explicit opt-out
        ]
        ok = True
        for c in blocked:
            hit = bool(PATTERN.search(c)) and OPT_OUT not in c
            print(("PASS " if hit else "FAIL ") + "block  " + c)
            ok &= hit
        for c in allowed:
            hit = bool(PATTERN.search(c)) and OPT_OUT not in c
            print(("PASS " if not hit else "FAIL ") + "allow  " + c)
            ok &= not hit
        sys.exit(0 if ok else 1)
    sys.exit(main())
