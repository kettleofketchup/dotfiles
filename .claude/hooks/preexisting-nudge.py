#!/usr/bin/env python3
"""Stop hook: push back when a turn waves something off as "pre-existing".

Fires when Claude finishes responding. If Claude's final message describes a
problem as *pre-existing* (a favourite way to dismiss a real issue — a failing
test, a lint error, formatting drift, a latent bug — on the grounds that it
predates the current change), this blocks the stop and reminds Claude that
being pre-existing almost never justifies leaving it: fix it regardless, or
explicitly get the user's sign-off to leave it.

Wiring (user-global, in dotfiles): registered as a `Stop` hook in
~/.claude/settings.local.json -> command points at this file. Input arrives as
JSON on stdin (see https://docs.claude.com/en/docs/claude-code/hooks); a
`{"decision":"block","reason":...}` object on stdout feeds `reason` back to
Claude and makes it keep working instead of ending the turn.
"""

import json
import re
import sys

# Matches "pre-existing", "preexisting", "pre existing" (any case).
PATTERN = re.compile(r"pre[-\s]?existing", re.IGNORECASE)

REASON = (
    'You called something "pre-existing". That is almost never a reason to '
    "leave it alone — pre-existing does NOT mean it does not matter. Re-examine "
    "the exact thing you just labelled pre-existing (a failing test, a lint "
    "error, formatting drift, a bug) and fix it regardless. Only leave it if you "
    "have explicitly checked with the user and they said to; do not dismiss it "
    "just because it predates your change."
)


def last_assistant_text(transcript_path):
    """Return the text of the most recent assistant message in the transcript."""
    if not transcript_path:
        return ""
    try:
        with open(transcript_path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return ""

    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "assistant":
            continue
        content = entry.get("message", {}).get("content", "")
        if isinstance(content, str):
            return content
        parts = []
        for block in content or []:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)
    return ""


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # never break the turn on malformed input

    # Loop guard: if we already blocked once and Claude is continuing from that,
    # don't block again on the same nudge.
    if payload.get("stop_hook_active"):
        sys.exit(0)

    text = last_assistant_text(payload.get("transcript_path", ""))
    if not text or not PATTERN.search(text):
        sys.exit(0)

    json.dump({"decision": "block", "reason": REASON}, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
