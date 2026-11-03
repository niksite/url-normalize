"""Execute the README's Python snippets and check their documented output."""

from pathlib import Path

import pytest

README = Path(__file__).resolve().parents[1] / "README.md"
OUTPUT_PREFIX = "# Output: "


def readme_examples():
    """Collect the README's unindented, triple-backtick Python fences."""
    lines = README.read_text(encoding="utf-8").splitlines()
    examples = []
    start = None
    for index, line in enumerate(lines):
        if line == "```python":
            assert start is None, "Unclosed Python example in README.md"
            start = index + 1
        elif start is not None and line == "```":
            examples.append(
                pytest.param(
                    start,
                    "\n".join(lines[start:index]),
                    id=f"README.md:{start + 1}",
                )
            )
            start = None
    assert start is None, "Unclosed Python example in README.md"
    assert examples, "No Python examples found in README.md"
    return examples


@pytest.mark.parametrize(("line_offset", "source"), readme_examples())
def test_readme_python_example(line_offset, source, capsys):
    """Require each copyable block to work alone and print its stated output."""
    # Execute trusted repository documentation, preserving traceback line numbers.
    code = compile("\n" * line_offset + source, str(README), "exec")
    exec(code, {})  # noqa: S102 - exercise the actual documented code
    captured = capsys.readouterr()
    expected = "".join(
        line.removeprefix(OUTPUT_PREFIX) + "\n"
        for line in source.splitlines()
        if line.startswith(OUTPUT_PREFIX)
    )
    assert captured.out == expected
    assert captured.err == ""
