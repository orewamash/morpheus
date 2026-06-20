"""
tests/test_static_analyzer.py — Tests for tree-sitter static analysis.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from morpheus.ml.static_analyzer import (
    StaticAnalysis,
    analyze_file,
    format_static_context,
)


# ---------------------------------------------------------------------------
#  Python analysis tests
# ---------------------------------------------------------------------------


class TestAnalyzePython:
    def test_detects_functions(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("def foo():\n    pass\n\ndef bar(x):\n    return x + 1\n")
            path = f.name

        result = analyze_file(path)
        assert result.language == "python"
        func_names = [fn["name"] for fn in result.functions]
        assert "foo" in func_names
        assert "bar" in func_names
        Path(path).unlink()

    def test_detects_classes(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("class MyClass:\n    def method(self):\n        pass\n")
            path = f.name

        result = analyze_file(path)
        assert len(result.classes) >= 1
        assert result.classes[0]["name"] == "MyClass"
        Path(path).unlink()

    def test_detects_imports(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("import os\nimport sys\nfrom pathlib import Path\n")
            path = f.name

        result = analyze_file(path)
        assert "os" in result.imports
        assert "sys" in result.imports
        Path(path).unlink()

    def test_complexity_hints(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("x = 1\n")
            path = f.name

        result = analyze_file(path)
        assert result.complexity_hints.get("line_count", 0) >= 1
        Path(path).unlink()

    def test_file_not_found(self):
        result = analyze_file("/nonexistent/file.py")
        assert "File not found" in result.error

    def test_unknown_extension(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xyz", delete=False
        ) as f:
            f.write("some content")
            path = f.name

        result = analyze_file(path)
        assert result.language == "unknown"
        Path(path).unlink()

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            path = f.name

        result = analyze_file(path)
        assert result.functions == []
        Path(path).unlink()


# ---------------------------------------------------------------------------
#  JavaScript analysis tests
# ---------------------------------------------------------------------------


class TestAnalyzeJavaScript:
    def test_detects_functions(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False
        ) as f:
            f.write("function hello() { return 1; }\nconst add = (a, b) => a + b;\n")
            path = f.name

        result = analyze_file(path)
        func_names = [fn["name"] for fn in result.functions]
        assert "hello" in func_names
        Path(path).unlink()

    def test_detects_classes(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False
        ) as f:
            f.write("class MyClass { constructor() {} }\n")
            path = f.name

        result = analyze_file(path)
        assert len(result.classes) >= 1
        Path(path).unlink()


# ---------------------------------------------------------------------------
#  C analysis tests
# ---------------------------------------------------------------------------


class TestAnalyzeC:
    def test_detects_functions(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".c", delete=False
        ) as f:
            f.write("int main() { return 0; }\nvoid helper(int x) { }\n")
            path = f.name

        result = analyze_file(path)
        func_names = [fn["name"] for fn in result.functions]
        assert "main" in func_names
        assert "helper" in func_names
        Path(path).unlink()


# ---------------------------------------------------------------------------
#  Format tests
# ---------------------------------------------------------------------------


class TestFormatStaticContext:
    def test_error_case(self):
        ctx = format_static_context(StaticAnalysis(language="python", error="oops"))
        assert "unavailable" in ctx

    def test_empty_analysis(self):
        ctx = format_static_context(StaticAnalysis(language="python"))
        assert "Static Code Analysis" in ctx

    def test_includes_function_names(self):
        an = StaticAnalysis(
            language="python",
            functions=[
                {"name": "foo", "start_line": 1},
                {"name": "bar", "start_line": 5},
            ],
        )
        ctx = format_static_context(an)
        assert "foo" in ctx
        assert "bar" in ctx

    def test_includes_imports(self):
        an = StaticAnalysis(language="python", imports=["os", "sys"])
        ctx = format_static_context(an)
        assert "os" in ctx

    def test_truncates_many_functions(self):
        functions = [
            {"name": f"fn_{i}", "start_line": i} for i in range(20)
        ]
        an = StaticAnalysis(language="python", functions=functions)
        ctx = format_static_context(an)
        assert "fn_0" in ctx
        assert "more" in ctx
