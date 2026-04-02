"""Tests for scripts/agent_diff_review.py extract_structure — 15 pure tests."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from agent_diff_review import extract_structure


class TestExtractStructureEmpty:
    def test_empty_source(self):
        result = extract_structure("")
        assert result == {}

    def test_whitespace_only(self):
        result = extract_structure("   \n\n  ")
        assert result == {}


class TestExtractStructureFunction:
    def test_single_function(self):
        src = "def foo():\n    pass\n"
        result = extract_structure(src)
        assert "foo" in result
        assert result["foo"]["type"] == "function"

    def test_function_args(self):
        src = "def bar(x, y, z):\n    return x + y + z\n"
        result = extract_structure(src)
        assert result["bar"]["args"] == ["x", "y", "z"]

    def test_has_return_true(self):
        src = "def f():\n    return 42\n"
        result = extract_structure(src)
        assert result["f"]["has_return"] is True

    def test_has_return_false(self):
        src = "def f():\n    pass\n"
        result = extract_structure(src)
        assert result["f"]["has_return"] is False

    def test_lineno(self):
        src = "\n\ndef f():\n    pass\n"
        result = extract_structure(src)
        assert result["f"]["lineno"] == 3

    def test_multiple_functions(self):
        src = "def a():\n    pass\ndef b():\n    pass\n"
        result = extract_structure(src)
        assert "a" in result
        assert "b" in result
        assert len(result) == 2

    def test_nested_return_counts_as_true(self):
        src = (
            "def outer():\n"
            "    def inner():\n"
            "        return 1\n"
            "    inner()\n"
        )
        result = extract_structure(src)
        # ast.walk visits nested nodes, so outer sees inner's return
        assert result["outer"]["has_return"] is True
        assert result["inner"]["has_return"] is True


class TestExtractStructureClass:
    def test_class_detected(self):
        src = "class Foo:\n    pass\n"
        result = extract_structure(src)
        assert "Foo" in result
        assert result["Foo"]["type"] == "class"

    def test_class_methods(self):
        src = "class Foo:\n    def bar(self):\n        pass\n"
        result = extract_structure(src)
        assert result["Foo"]["methods"] == ["bar"]

    def test_class_with_method_both_entries(self):
        src = "class Foo:\n    def bar(self):\n        return 1\n"
        result = extract_structure(src)
        # ast.walk produces both class and function entries
        assert "Foo" in result
        assert "bar" in result
        assert len(result) == 2


class TestExtractStructureSyntaxError:
    def test_syntax_error_returns_none(self):
        result = extract_structure("def (broken")
        assert result is None


class TestExtractStructureNoArgs:
    def test_function_no_args(self):
        src = "def solo():\n    return True\n"
        result = extract_structure(src)
        assert result["solo"]["args"] == []


class TestExtractStructureComplex:
    def test_classes_without_methods(self):
        src = (
            "class A:\n    x = 1\n"
            "class B:\n    y = 2\n"
            "class C:\n    z = 3\n"
            "def f1():\n    pass\n"
            "def f2():\n    pass\n"
        )
        result = extract_structure(src)
        assert len(result) == 5
        for name in ["A", "B", "C", "f1", "f2"]:
            assert name in result
