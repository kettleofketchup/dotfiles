from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENT = ROOT / "agents" / "comment-reviewer.md"
COMMAND = ROOT / "commands" / "comment-review.md"


def test_agent_grants_the_tools_it_needs():
    """Without Edit and Bash the agent cannot rewrite a comment or commit."""
    front = AGENT.read_text().split("---")[1]
    for tool in ("Read", "Edit", "Bash", "Glob", "Grep"):
        assert tool in front


def test_agent_pins_the_commit_message_and_forbids_trailers():
    body = AGENT.read_text()
    assert "comments:" in body
    assert "Co-Authored-By" in body      # mentioned in order to forbid it
    assert "no watermark" in body.lower()


def test_agent_forbids_commit_all_flags():
    body = AGENT.read_text()
    assert "git commit -a" in body       # named as forbidden
    assert "explicit" in body.lower()


def test_agent_states_the_no_receipt_failure_paths():
    body = AGENT.read_text()
    for condition in ("base_unresolved", "in progress", "commit fail"):
        assert condition.lower() in body.lower()


def test_agent_uses_the_plugin_root_variable_for_scripts():
    assert "${CLAUDE_PLUGIN_ROOT}" in AGENT.read_text()


def test_command_only_dispatches_the_agent():
    """The method lives in one place. A command that re-explains the rules is a
    second copy that will drift."""
    body = COMMAND.read_text()
    assert "comment-reviewer" in body
    assert len(body.splitlines()) <= 40
