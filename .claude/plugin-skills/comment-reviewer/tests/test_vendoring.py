"""hooks/scripts/ and skills/.../scripts/ install to unrelated paths and cannot
import each other, so gitpaths.py is vendored to both. Drift between them is a
silent split-brain bug: the gate and the reviewer would disagree about where
receipts live."""

import paths


def test_gitpaths_copies_are_byte_identical():
    source = (paths.SCRIPTS / "gitpaths.py").read_bytes()
    vendored = (paths.HOOK_SCRIPTS / "gitpaths.py").read_bytes()
    assert source == vendored, "run: cp scripts/gitpaths.py hooks/scripts/gitpaths.py"
