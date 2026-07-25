from pathlib import Path

import extract_comments as ec
import paths


def spans(name):
    return ec.extract(paths.SAMPLES / name)["comments"]


def texts(name):
    return [c["text"] for c in spans(name)]


def test_go_line_and_block_spans():
    result = spans("sample.go")
    first = result[0]
    assert (first["start_line"], first["end_line"], first["kind"]) == (1, 1, "line")
    block = [c for c in result if c["kind"] == "block"]
    assert len(block) == 1
    assert (block[0]["start_line"], block[0]["end_line"]) == (4, 5)


def test_go_ignores_double_slash_inside_strings():
    """The positive count is load-bearing: every `assert not any(...)` below
    passes trivially on an empty list, which is exactly what happened when the
    samples lived in a directory the extractor skips."""
    found = texts("sample.go")
    assert len(found) == 3          # leading, block, trailing
    assert not any("example.com" in t for t in found)
    assert not any("back" in t for t in found)


def test_go_finds_the_trailing_comment():
    assert any("trailing" in t for t in texts("sample.go"))


def test_python_ignores_hash_inside_strings():
    found = texts("sample.py")
    assert len(found) == 4          # module docstring, line, fn docstring, trailing
    assert not any("not a comment" in t for t in found)
    assert not any("single" in t for t in found)


def test_python_captures_the_module_docstring_span():
    docstrings = [c for c in spans("sample.py") if "Module docstring" in c["text"]]
    assert len(docstrings) == 1
    assert (docstrings[0]["start_line"], docstrings[0]["end_line"]) == (1, 2)
    assert docstrings[0]["kind"] == "docstring"


def test_python_captures_the_function_docstring():
    docstrings = [c for c in spans("sample.py") if "Function docstring" in c["text"]]
    assert len(docstrings) == 1
    assert docstrings[0]["start_line"] == 12
    assert docstrings[0]["kind"] == "docstring"


def test_python_leaves_a_triple_quoted_data_string_alone():
    """A triple-quoted literal that is not in docstring position is data. Emitting
    it as a comment would invite the reviewer to rewrite a live string."""
    found = texts("sample.py")
    assert len(found) == 4
    assert not any("not a docstring" in t for t in found)
    assert not any("just data" in t for t in found)


def test_python_line_comment_after_the_docstring():
    leading = [c for c in spans("sample.py") if "leading comment" in c["text"]]
    assert len(leading) == 1
    assert leading[0]["start_line"] == 4 and leading[0]["kind"] == "line"


def test_shell_ignores_hash_inside_quotes():
    found = texts("sample.sh")
    assert len(found) == 2          # shebang, real comment
    assert not any("inside quotes" in t for t in found)


def test_sql_double_dash():
    assert len(texts("sample.sql")) == 2


def test_typescript_ignores_slashes_in_strings():
    found = texts("sample.ts")
    assert len(found) == 2          # line, block
    assert not any("inside" in t for t in found)


def test_yaml_finds_the_comment_after_an_apostrophe():
    """An apostrophe in prose used to open a string that swallowed the rest of
    the file."""
    assert any("trailing" in t for t in texts("sample.yaml"))


def test_html_finds_the_comment_after_an_apostrophe():
    assert any("trailing" in t for t in texts("sample.html"))


def test_rust_nested_block_span_covers_the_whole_comment():
    block = [c for c in spans("sample.rs") if c["kind"] == "block"][0]
    assert block["text"].endswith("*/")
    assert block["text"].count("/*") == 2


def test_lua_long_bracket_comment_is_one_block():
    assert any(c["kind"] == "block" for c in spans("sample.lua"))


def test_nix_finds_its_comments():
    assert len(texts("sample.nix")) >= 2


def test_multi_language_files_are_skipped_not_half_scanned(tmp_path):
    """A .vue file needs per-block token selection; scanning it with the HTML
    table would silently miss every comment in its script block."""
    target = tmp_path / "c.vue"
    target.write_text("<template><!-- t --></template>\n<script>// s\n</script>\n")
    assert ec.extract(target)["skipped"] == "multi-language-unsupported"


def test_detect_language_by_extension():
    assert ec.detect_language(Path("a.go")) == "go"
    assert ec.detect_language(Path("a.tsx")) == "typescript"


def test_detect_language_by_shebang(tmp_path):
    script = tmp_path / "noext"
    script.write_text("#!/usr/bin/env python3\n# hi\n")
    assert ec.detect_language(script) == "python"


def test_unknown_extension_is_skipped_not_guessed(tmp_path):
    odd = tmp_path / "a.qqq"
    odd.write_text("// hi\n")
    assert ec.extract(odd)["skipped"] == "unknown-language"


def test_binary_file_is_skipped(tmp_path):
    blob = tmp_path / "a.go"
    blob.write_bytes(b"package main\x00\x00binary")
    assert ec.extract(blob)["skipped"] == "binary"


def test_oversized_file_is_skipped(tmp_path):
    big = tmp_path / "big.go"
    big.write_text("// c\n" + "x = 1\n" * 200_000)
    assert ec.extract(big)["skipped"] == "too-large"


def test_missing_file_is_skipped(tmp_path):
    assert ec.extract(tmp_path / "gone.go")["skipped"] == "unreadable"


def test_markdown_is_out_of_scope(tmp_path):
    doc = tmp_path / "a.md"
    doc.write_text("<!-- hi -->\n")
    assert ec.extract(doc)["skipped"] == "markdown-out-of-scope"


def test_main_reads_paths_from_stdin(tmp_path, capsys, monkeypatch):
    import io, json, sys
    target = paths.SAMPLES / "sample.go"
    monkeypatch.setattr(sys, "stdin", io.StringIO(f"{target}\n"))
    ec.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["files"][0]["lang"] == "go"
