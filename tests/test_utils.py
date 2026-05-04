"""Tests for GuardPilot utility functions."""

import json
import os
import tempfile
import unittest

from guardpilot.utils import (
    Colors,
    YAMLParseError,
    bold_text,
    calculate_similarity,
    colored_text,
    format_timestamp,
    load_file,
    load_json,
    load_yaml,
    parse_yaml,
)


class TestColoredText(unittest.TestCase):
    """Tests for ANSI color text functions."""

    def test_colored_text(self):
        """Test colored_text wraps text with ANSI codes."""
        result = colored_text("hello", Colors.RED)
        self.assertTrue(result.startswith(Colors.RED))
        self.assertTrue(result.endswith(Colors.RESET))
        self.assertIn("hello", result)

    def test_bold_text(self):
        """Test bold_text wraps text with bold ANSI codes."""
        result = bold_text("hello")
        self.assertTrue(result.startswith(Colors.BOLD))
        self.assertTrue(result.endswith(Colors.RESET))

    def test_reset_in_result(self):
        """Test that RESET is always appended."""
        result = colored_text("test", Colors.GREEN)
        self.assertTrue(result.endswith(Colors.RESET))


class TestFormatTimestamp(unittest.TestCase):
    """Tests for timestamp formatting."""

    def test_returns_string(self):
        """Test format_timestamp returns a string."""
        result = format_timestamp()
        self.assertIsInstance(result, str)

    def test_contains_iso_format(self):
        """Test format_timestamp returns ISO format."""
        result = format_timestamp()
        self.assertIn("T", result)


class TestCalculateSimilarity(unittest.TestCase):
    """Tests for Jaccard word similarity."""

    def test_identical_texts(self):
        """Test similarity of identical texts is 1.0."""
        score = calculate_similarity("hello world", "hello world")
        self.assertEqual(score, 1.0)

    def test_no_overlap(self):
        """Test similarity of completely different texts."""
        score = calculate_similarity("hello world", "foo bar baz")
        self.assertEqual(score, 0.0)

    def test_partial_overlap(self):
        """Test similarity with partial word overlap."""
        score = calculate_similarity("hello world foo", "hello bar baz")
        self.assertGreater(score, 0.0)
        self.assertLess(score, 1.0)

    def test_empty_string(self):
        """Test similarity with empty string returns 0.0."""
        self.assertEqual(calculate_similarity("", "hello"), 0.0)
        self.assertEqual(calculate_similarity("hello", ""), 0.0)

    def test_case_insensitive(self):
        """Test similarity is case-insensitive."""
        s1 = calculate_similarity("Hello World", "hello world")
        self.assertEqual(s1, 1.0)


class TestYAMLParser(unittest.TestCase):
    """Tests for the minimal YAML subset parser."""

    def test_empty_string(self):
        """Test parsing empty string returns empty dict."""
        result = parse_yaml("")
        self.assertEqual(result, {})

    def test_simple_mapping(self):
        """Test parsing a simple key-value mapping."""
        yaml_text = "key: value"
        result = parse_yaml(yaml_text)
        self.assertEqual(result, {"key": "value"})

    def test_multiple_keys(self):
        """Test parsing multiple key-value pairs."""
        yaml_text = "name: test\nvalue: 42"
        result = parse_yaml(yaml_text)
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["value"], 42)

    def test_nested_mapping(self):
        """Test parsing nested mappings."""
        yaml_text = "outer:\n  inner: value"
        result = parse_yaml(yaml_text)
        self.assertEqual(result["outer"]["inner"], "value")

    def test_simple_list(self):
        """Test parsing a simple list."""
        yaml_text = "- item1\n- item2\n- item3"
        result = parse_yaml(yaml_text)
        self.assertEqual(result, ["item1", "item2", "item3"])

    def test_list_of_mappings(self):
        """Test parsing a list of mappings."""
        yaml_text = "- name: alice\n  age: 30\n- name: bob\n  age: 25"
        result = parse_yaml(yaml_text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "alice")
        self.assertEqual(result[0]["age"], 30)
        self.assertEqual(result[1]["name"], "bob")

    def test_boolean_values(self):
        """Test parsing boolean values."""
        yaml_text = "enabled: true\ndisabled: false"
        result = parse_yaml(yaml_text)
        self.assertTrue(result["enabled"])
        self.assertFalse(result["disabled"])

    def test_null_values(self):
        """Test parsing null values."""
        yaml_text = "value: null\nother: ~"
        result = parse_yaml(yaml_text)
        self.assertIsNone(result["value"])
        self.assertIsNone(result["other"])

    def test_quoted_strings(self):
        """Test parsing quoted strings."""
        yaml_text = 'single: \'hello world\'\ndouble: "hello world"'
        result = parse_yaml(yaml_text)
        self.assertEqual(result["single"], "hello world")
        self.assertEqual(result["double"], "hello world")

    def test_comments_stripped(self):
        """Test that comments are stripped from YAML."""
        yaml_text = "key: value # this is a comment\nother: test"
        result = parse_yaml(yaml_text)
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["other"], "test")

    def test_numbers(self):
        """Test parsing integer and float values."""
        yaml_text = "int: 42\nfloat: 3.14\nneg: -10"
        result = parse_yaml(yaml_text)
        self.assertEqual(result["int"], 42)
        self.assertAlmostEqual(result["float"], 3.14)
        self.assertEqual(result["neg"], -10)

    def test_yes_no_booleans(self):
        """Test yes/no as boolean values."""
        yaml_text = "a: yes\nb: no"
        result = parse_yaml(yaml_text)
        self.assertTrue(result["a"])
        self.assertFalse(result["b"])

    def test_complex_nested_structure(self):
        """Test parsing complex nested YAML structure."""
        yaml_text = """
rules:
  - id: rule1
    name: First Rule
    priority: high
    conditions:
      - type: keyword
        value: test
        negate: true
  - id: rule2
    name: Second Rule
    priority: low
"""
        result = parse_yaml(yaml_text)
        self.assertIn("rules", result)
        self.assertEqual(len(result["rules"]), 2)
        self.assertEqual(result["rules"][0]["id"], "rule1")
        self.assertEqual(result["rules"][0]["conditions"][0]["type"], "keyword")
        self.assertTrue(result["rules"][0]["conditions"][0]["negate"])

    def test_inline_list_values(self):
        """Test parsing inline list-like values."""
        yaml_text = "items:\n  - a\n  - b\n  - c"
        result = parse_yaml(yaml_text)
        self.assertEqual(result["items"], ["a", "b", "c"])


class TestLoadYAML(unittest.TestCase):
    """Tests for loading YAML files."""

    def test_load_valid_yaml_file(self):
        """Test loading a valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("key: value\nnumber: 42")
            f.flush()
            result = load_yaml(f.name)
        os.unlink(f.name)
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["number"], 42)

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_yaml("/nonexistent/path.yaml")


class TestLoadJSON(unittest.TestCase):
    """Tests for loading JSON files."""

    def test_load_valid_json_file(self):
        """Test loading a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value", "number": 42}, f)
            f.flush()
            result = load_json(f.name)
        os.unlink(f.name)
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["number"], 42)

    def test_load_nonexistent_json(self):
        """Test loading a nonexistent JSON file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_json("/nonexistent/path.json")


class TestLoadFile(unittest.TestCase):
    """Tests for the generic file loader."""

    def test_load_yaml_file(self):
        """Test loading a .yaml file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("key: value")
            f.flush()
            result = load_file(f.name)
        os.unlink(f.name)
        self.assertEqual(result["key"], "value")

    def test_load_yml_file(self):
        """Test loading a .yml file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("key: value")
            f.flush()
            result = load_file(f.name)
        os.unlink(f.name)
        self.assertEqual(result["key"], "value")

    def test_load_json_file(self):
        """Test loading a .json file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            result = load_file(f.name)
        os.unlink(f.name)
        self.assertEqual(result["key"], "value")

    def test_unsupported_format(self):
        """Test loading an unsupported file format raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some text")
            f.flush()
            with self.assertRaises(ValueError):
                load_file(f.name)
        os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
