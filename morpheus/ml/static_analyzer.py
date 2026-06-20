"""
morpheus/ml/static_analyzer.py — Tree-sitter AST analysis for enhanced Oracle narration.

Extracts structural metadata from source files to complement dynamic tracing:
  - Function and method definitions
  - Call graph (which functions call which)
  - Class definitions and their methods
  - Import/require statements
  - Complexity hints (nesting depth, branching)

Gracefully degrades when tree-sitter libraries are not installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StaticAnalysis:
    """
    Results of static AST analysis on a source file.

    Compatible across Python, JavaScript, TypeScript, C, C++, and Java.
    """

    language: str
    functions: list[dict[str, Any]] = field(default_factory=list)
    classes: list[dict[str, Any]] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    complexity_hints: dict[str, Any] = field(default_factory=dict)
    error: str = ""


# ---------------------------------------------------------------------------
#  Language-specific query patterns (tree-sitter DSL)
# ---------------------------------------------------------------------------

_LANG_CONFIG: dict[str, dict[str, Any]] = {
    "python": {
        "lang_module": "tree_sitter_python",
        "function_query": "(function_definition name: (identifier) @name) @node",
        "class_query": "(class_definition name: (identifier) @name) @node",
        "call_query": "(call function: (identifier) @name) @node",
        "import_query": "(import_statement (dotted_name) @name) @node",
    },
    "javascript": {
        "lang_module": "tree_sitter_javascript",
        "function_query": "[(function_declaration name: (identifier) @name) @node (arrow_function) @node]",
        "class_query": "(class_declaration name: (identifier) @name) @node",
        "call_query": "(call_expression function: (identifier) @name) @node",
        "import_query": "(import_statement source: (string) @name) @node",
    },
    "typescript": {
        "lang_module": "tree_sitter_javascript",
        "function_query": "[(function_declaration name: (identifier) @name) @node (arrow_function) @node]",
        "class_query": "(class_declaration name: (identifier) @name) @node",
        "call_query": "(call_expression function: (identifier) @name) @node",
        "import_query": "(import_statement source: (string) @name) @node",
    },
    "c": {
        "lang_module": "tree_sitter_c",
        "function_query": "(function_definition declarator: (function_declarator declarator: (identifier) @name)) @node",
        "call_query": "(call_expression function: (identifier) @name) @node",
        "import_query": "(preproc_include path: (string_literal) @name) @node",
    },
    "cpp": {
        "lang_module": "tree_sitter_cpp",
        "function_query": "(function_definition declarator: (function_declarator declarator: (identifier) @name)) @node",
        "class_query": "(class_specifier name: (type_identifier) @name) @node",
        "call_query": "(call_expression function: (identifier) @name) @node",
        "import_query": "(preproc_include path: (string_literal) @name) @node",
    },
    "java": {
        "lang_module": "tree_sitter_java",
        "function_query": "[(method_declaration name: (identifier) @name) @node (constructor_declaration name: (identifier) @name) @node]",
        "class_query": "(class_declaration name: (identifier) @name) @node",
        "call_query": "(method_invocation name: (identifier) @name) @node",
        "import_query": "(import_declaration (identifier) @name) @node",
    },
}


def analyze_file(filepath: str) -> StaticAnalysis:
    """
    Parse a source file with tree-sitter and return structural metadata.

    Falls back to regex-based heuristics when tree-sitter is not installed.

    Args:
        filepath: Path to the source file.

    Returns:
        StaticAnalysis dataclass with extracted metadata.
    """
    resolved = Path(filepath).resolve()
    if not resolved.exists():
        return StaticAnalysis(language=_guess_language(filepath), error="File not found")

    source = resolved.read_text(encoding="utf-8", errors="replace")
    lang = _guess_language(filepath)

    # Try tree-sitter first
    result = _analyze_with_treesitter(source, lang)
    if result is not None:
        return result

    # Fallback: regex-based heuristics
    return _analyze_with_regex(source, lang)


def _guess_language(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()
    _map = {
        ".py": "python",
        ".pyw": "python",
        ".js": "javascript",
        ".mjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".java": "java",
    }
    return _map.get(ext, "unknown")


def _analyze_with_treesitter(source: str, language: str) -> StaticAnalysis | None:
    """Try tree-sitter parsing. Returns None if libraries are missing."""
    try:
        import tree_sitter  # noqa: E402
    except ImportError:
        return None

    config = _LANG_CONFIG.get(language)
    if config is None:
        return None

    # Lazy-import the language grammar
    try:
        lang_module = __import__(config["lang_module"], fromlist=["language"])
        lang = lang_module.language()
    except (ImportError, AttributeError):
        # Fallback: try py-tree-sitter 0.23+ API
        try:
            from tree_sitter import Language  # noqa: E402

            lang = Language(config["lang_module"])
        except (ImportError, Exception):
            return None

    try:
        parser = tree_sitter.Parser()
        parser.set_language(lang)
        tree = parser.parse(bytes(source, "utf-8"))
    except Exception:
        return None

    analysis = StaticAnalysis(language=language)

    def _extract_nodes(query_str: str) -> list[dict[str, Any]]:
        if not query_str:
            return []
        try:
            query = lang.query(query_str)
            captures = query.captures(tree.root_node)
            results: list[dict[str, Any]] = []
            seen: set[str] = set()
            for node, tag in captures:
                if tag != "name":
                    continue
                name = source[node.start_byte : node.end_byte]
                if name in seen:
                    continue
                seen.add(name)
                results.append(
                    {
                        "name": name,
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                    }
                )
            return results
        except Exception:
            return []

    analysis.functions = _extract_nodes(config.get("function_query", ""))
    analysis.classes = _extract_nodes(config.get("class_query", ""))
    analysis.imports = [
        c.get("name", "")
        for c in _extract_nodes(config.get("import_query", ""))
        if c.get("name")
    ]

    # Extract function -> function calls (call graph)
    call_names = _extract_nodes(config.get("call_query", ""))
    analysis.calls = [
        {"source": "?", "target": c["name"], "line": c.get("start_line", 0)}
        for c in call_names
    ]

    # Complexity hints
    lines = source.split("\n")
    analysis.complexity_hints = {
        "line_count": len(lines),
        "function_count": len(analysis.functions),
        "class_count": len(analysis.classes),
        "import_count": len(analysis.imports),
    }

    return analysis


def _analyze_with_regex(source: str, language: str) -> StaticAnalysis:
    """Fallback: simple regex-based structural analysis."""
    import re  # noqa: E402

    analysis = StaticAnalysis(language=language)

    if language == "python":
        func_pattern = re.compile(r"^def\s+(\w+)\s*\(", re.MULTILINE)
        class_pattern = re.compile(r"^class\s+(\w+)", re.MULTILINE)
        import_pattern = re.compile(r"^(?:from\s+(\S+)\s+)?import\s+(\S+)", re.MULTILINE)

        for m in func_pattern.finditer(source):
            analysis.functions.append(
                {
                    "name": m.group(1),
                    "start_line": source[: m.start()].count("\n") + 1,
                }
            )
        for m in class_pattern.finditer(source):
            analysis.classes.append(
                {
                    "name": m.group(1),
                    "start_line": source[: m.start()].count("\n") + 1,
                }
            )
        for m in import_pattern.finditer(source):
            prefix = m.group(1) or ""
            target = m.group(2) or ""
            full = f"{prefix}.{target}" if prefix else target
            analysis.imports.append(full)

    elif language in ("javascript", "typescript"):
        func_pattern = re.compile(
            r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\()",
            re.MULTILINE,
        )
        class_pattern = re.compile(r"class\s+(\w+)", re.MULTILINE)
        for m in func_pattern.finditer(source):
            name = m.group(1) or m.group(2)
            if name:
                analysis.functions.append(
                    {
                        "name": name,
                        "start_line": source[: m.start()].count("\n") + 1,
                    }
                )
        for m in class_pattern.finditer(source):
            analysis.classes.append(
                {
                    "name": m.group(1),
                    "start_line": source[: m.start()].count("\n") + 1,
                }
            )

    elif language in ("c", "cpp"):
        func_pattern = re.compile(
            r"(?:int|void|char|float|double|long|size_t|bool)\s+(\w+)\s*\(",
            re.MULTILINE,
        )
        for m in func_pattern.finditer(source):
            analysis.functions.append(
                {
                    "name": m.group(1),
                    "start_line": source[: m.start()].count("\n") + 1,
                }
            )

    elif language == "java":
        func_pattern = re.compile(
            r"(?:public|private|protected|static)?\s*(?:\w+\s+)?(\w+)\s*\(",
            re.MULTILINE,
        )
        class_pattern = re.compile(r"(?:public\s+)?(?:class|interface)\s+(\w+)", re.MULTILINE)
        for m in func_pattern.finditer(source):
            kw = m.group(1)
            if kw and kw not in (
                "if",
                "for",
                "while",
                "switch",
                "catch",
                "return",
            ):
                analysis.functions.append(
                    {
                        "name": kw,
                        "start_line": source[: m.start()].count("\n") + 1,
                    }
                )
        for m in class_pattern.finditer(source):
            analysis.classes.append(
                {
                    "name": m.group(1),
                    "start_line": source[: m.start()].count("\n") + 1,
                }
            )

    lines = source.split("\n")
    analysis.complexity_hints = {
        "line_count": len(lines),
        "function_count": len(analysis.functions),
        "class_count": len(analysis.classes),
    }

    return analysis


def format_static_context(analysis: StaticAnalysis) -> str:
    """
    Format a StaticAnalysis into a human-readable context string for LLM prompts.
    """
    if analysis.error:
        return f"[Static analysis unavailable: {analysis.error}]"

    parts: list[str] = ["--- Static Code Analysis ---"]

    if analysis.imports:
        parts.append(f"Imports ({len(analysis.imports)}): {', '.join(analysis.imports[:15])}")
        if len(analysis.imports) > 15:
            parts.append(f"  ... and {len(analysis.imports) - 15} more")

    if analysis.functions:
        parts.append(f"Functions ({len(analysis.functions)}):")
        for fn in analysis.functions[:10]:
            parts.append(f"  {fn['name']} (line {fn.get('start_line', '?')})")
        if len(analysis.functions) > 10:
            parts.append(f"  ... and {len(analysis.functions) - 10} more")

    if analysis.classes:
        parts.append(f"Classes ({len(analysis.classes)}):")
        for cls in analysis.classes[:5]:
            parts.append(f"  {cls['name']} (line {cls.get('start_line', '?')})")

    if analysis.calls:
        call_targets = list({c["target"] for c in analysis.calls[:20]})
        parts.append(f"Call targets: {', '.join(call_targets)}")

    hints = analysis.complexity_hints
    parts.append(
        f"Size: {hints.get('line_count', '?')} lines, "
        f"{hints.get('function_count', 0)} functions, "
        f"{hints.get('class_count', 0)} classes"
    )

    return "\n".join(parts)
