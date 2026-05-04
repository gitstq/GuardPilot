"""Tests for GuardPilot CLI commands."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from guardpilot.cli import build_parser, cmd_check, cmd_init, cmd_report, cmd_rules, cmd_validate, main


class TestBuildParser(unittest.TestCase):
    """Tests for argument parser construction."""

    def test_parser_exists(self):
        """Test parser is created successfully."""
        parser = build_parser()
        self.assertIsNotNone(parser)

    def test_version_flag(self):
        """Test --version flag."""
        parser = build_parser()
        with self.assertRaises(SystemExit) as ctx:
            parser.parse_args(["--version"])
        self.assertEqual(ctx.exception.code, 0)

    def test_no_command(self):
        """Test parser with no command."""
        parser = build_parser()
        args = parser.parse_args([])
        self.assertIsNone(args.command)


class TestCmdInit(unittest.TestCase):
    """Tests for the init command."""

    def test_init_creates_files(self):
        """Test init creates rules and conversation files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                output_path = os.path.join(tmpdir, "test_rules.yaml")
                args = type("Args", (), {"output": output_path})()
                ret = cmd_init(args)
                self.assertEqual(ret, 0)
                self.assertTrue(os.path.exists(output_path))
                conv_path = os.path.join(tmpdir, "example_conversation.json")
                self.assertTrue(os.path.exists(conv_path))
            finally:
                os.chdir(orig_cwd)

    def test_init_default_path(self):
        """Test init with default output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                args = type("Args", (), {"output": None})()
                ret = cmd_init(args)
                self.assertEqual(ret, 0)
                self.assertTrue(os.path.exists("guardpilot_rules.yaml"))
                self.assertTrue(os.path.exists("example_conversation.json"))
            finally:
                os.chdir(orig_cwd)


class TestCmdValidate(unittest.TestCase):
    """Tests for the validate command."""

    def _write_rules_file(self, content: str) -> str:
        """Write rules content to a temp file."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        f.write(content)
        f.flush()
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_validate_valid_rules(self):
        """Test validating a valid rules file."""
        yaml_content = """
rules:
  - id: test-1
    name: Test Rule
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value: test
"""
        path = self._write_rules_file(yaml_content)
        args = type("Args", (), {"file": path})()
        ret = cmd_validate(args)
        self.assertEqual(ret, 0)

    def test_validate_nonexistent_file(self):
        """Test validating a nonexistent file returns error."""
        args = type("Args", (), {"file": "/nonexistent/path.yaml"})()
        ret = cmd_validate(args)
        self.assertEqual(ret, 1)


class TestCmdCheck(unittest.TestCase):
    """Tests for the check command."""

    def _write_rules_file(self, content: str) -> str:
        """Write rules content to a temp file."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        f.write(content)
        f.flush()
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def _write_conv_file(self, data: dict) -> str:
        """Write conversation data to a temp JSON file."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(data, f)
        f.flush()
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_check_message_pass(self):
        """Test checking a clean message."""
        yaml_content = """
rules:
  - id: no-bad
    name: No Bad
    severity: block
    conditions:
      - type: keyword
        value: badword
        negate: true
"""
        rules_path = self._write_rules_file(yaml_content)
        args = type("Args", (), {
            "rules": rules_path,
            "message": "Hello, this is a clean message.",
            "conversation": None,
        })()
        ret = cmd_check(args)
        self.assertEqual(ret, 0)

    def test_check_message_fail(self):
        """Test checking a message with violations."""
        yaml_content = """
rules:
  - id: no-bad
    name: No Bad
    severity: block
    conditions:
      - type: keyword
        value: badword
        negate: true
"""
        rules_path = self._write_rules_file(yaml_content)
        args = type("Args", (), {
            "rules": rules_path,
            "message": "This contains a badword",
            "conversation": None,
        })()
        ret = cmd_check(args)
        self.assertEqual(ret, 2)

    def test_check_conversation(self):
        """Test checking a conversation file."""
        yaml_content = """
rules:
  - id: no-bad
    name: No Bad
    severity: block
    conditions:
      - type: keyword
        value: badword
        negate: true
"""
        rules_path = self._write_rules_file(yaml_content)
        conv_data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        }
        conv_path = self._write_conv_file(conv_data)
        args = type("Args", (), {
            "rules": rules_path,
            "message": None,
            "conversation": conv_path,
        })()
        ret = cmd_check(args)
        self.assertEqual(ret, 0)

    def test_check_missing_rules(self):
        """Test check without --rules returns error."""
        args = type("Args", (), {
            "rules": None,
            "message": "test",
            "conversation": None,
        })()
        ret = cmd_check(args)
        self.assertEqual(ret, 1)

    def test_check_missing_message_and_conversation(self):
        """Test check without --message or --conversation returns error."""
        yaml_content = """
rules:
  - id: test
    name: Test
    conditions:
      - type: keyword
        value: test
"""
        rules_path = self._write_rules_file(yaml_content)
        args = type("Args", (), {
            "rules": rules_path,
            "message": None,
            "conversation": None,
        })()
        ret = cmd_check(args)
        self.assertEqual(ret, 1)


class TestCmdReport(unittest.TestCase):
    """Tests for the report command."""

    def _write_rules_file(self, content: str) -> str:
        """Write rules content to a temp file."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        f.write(content)
        f.flush()
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def _write_conv_file(self, data: dict) -> str:
        """Write conversation data to a temp JSON file."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(data, f)
        f.flush()
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_report_markdown(self):
        """Test generating markdown report."""
        yaml_content = """
rules:
  - id: no-bad
    name: No Bad
    severity: block
    conditions:
      - type: keyword
        value: badword
        negate: true
"""
        rules_path = self._write_rules_file(yaml_content)
        conv_data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        }
        conv_path = self._write_conv_file(conv_data)
        args = type("Args", (), {
            "rules": rules_path,
            "conversation": conv_path,
            "format": "markdown",
            "output": None,
        })()
        ret = cmd_report(args)
        self.assertEqual(ret, 0)

    def test_report_json(self):
        """Test generating JSON report."""
        yaml_content = """
rules:
  - id: test
    name: Test
    severity: log
    conditions:
      - type: keyword
        value: hello
"""
        rules_path = self._write_rules_file(yaml_content)
        conv_data = {
            "messages": [
                {"role": "assistant", "content": "Hello world"},
            ]
        }
        conv_path = self._write_conv_file(conv_data)
        args = type("Args", (), {
            "rules": rules_path,
            "conversation": conv_path,
            "format": "json",
            "output": None,
        })()
        ret = cmd_report(args)
        self.assertEqual(ret, 0)

    def test_report_html_to_file(self):
        """Test generating HTML report to file."""
        yaml_content = """
rules:
  - id: test
    name: Test
    severity: log
    conditions:
      - type: keyword
        value: hello
"""
        rules_path = self._write_rules_file(yaml_content)
        conv_data = {
            "messages": [
                {"role": "assistant", "content": "Hello world"},
            ]
        }
        conv_path = self._write_conv_file(conv_data)

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as out_f:
            output_path = out_f.name
        self.addCleanup(os.unlink, output_path)

        args = type("Args", (), {
            "rules": rules_path,
            "conversation": conv_path,
            "format": "html",
            "output": output_path,
        })()
        ret = cmd_report(args)
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r') as f:
            content = f.read()
        self.assertIn("<!DOCTYPE html>", content)

    def test_report_missing_rules(self):
        """Test report without --rules returns error."""
        args = type("Args", (), {
            "rules": None,
            "conversation": "conv.json",
            "format": "markdown",
            "output": None,
        })()
        ret = cmd_report(args)
        self.assertEqual(ret, 1)


class TestCmdRules(unittest.TestCase):
    """Tests for the rules subcommands."""

    def _write_rules_file(self, content: str) -> str:
        """Write rules content to a temp file."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        f.write(content)
        f.flush()
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_rules_list(self):
        """Test listing rules."""
        yaml_content = """
rules:
  - id: test-1
    name: Test Rule One
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value: test
  - id: test-2
    name: Test Rule Two
    priority: low
    severity: log
    enabled: false
    conditions:
      - type: keyword
        value: other
"""
        rules_path = self._write_rules_file(yaml_content)
        args = type("Args", (), {
            "rules_action": "list",
            "rules": rules_path,
        })()
        ret = cmd_rules(args)
        self.assertEqual(ret, 0)

    def test_rules_list_missing_file(self):
        """Test rules list with missing file returns error."""
        args = type("Args", (), {
            "rules_action": "list",
            "rules": "/nonexistent/path.yaml",
        })()
        ret = cmd_rules(args)
        self.assertEqual(ret, 1)


class TestMain(unittest.TestCase):
    """Tests for the main entry point."""

    def test_main_no_args(self):
        """Test main with no arguments returns 0 (shows help)."""
        ret = main([])
        self.assertEqual(ret, 0)

    def test_main_init(self):
        """Test main with init command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                ret = main(["init"])
                self.assertEqual(ret, 0)
            finally:
                os.chdir(orig_cwd)

    def test_main_no_banner(self):
        """Test main with --no-banner flag."""
        ret = main(["--no-banner"])
        self.assertEqual(ret, 0)

    def test_main_unknown_command(self):
        """Test main with unknown command returns 1."""
        with self.assertRaises(SystemExit):
            main(["nonexistent"])


if __name__ == "__main__":
    unittest.main()
