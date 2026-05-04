"""Tests for GuardPilot rule engine."""

import json
import os
import tempfile
import unittest

from guardpilot.engine import RuleEngine
from guardpilot.models import (
    ComplianceResult,
    Condition,
    Conversation,
    Rule,
)


class TestRuleEngineInit(unittest.TestCase):
    """Tests for RuleEngine initialization."""

    def test_default_init(self):
        """Test engine initializes with empty rules."""
        engine = RuleEngine()
        self.assertEqual(engine.rules, [])


class TestLoadRules(unittest.TestCase):
    """Tests for loading rules from files."""

    def _write_rules_file(self, content: str) -> str:
        """Write rules content to a temp file and return the path."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        f.write(content)
        f.flush()
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_load_valid_rules(self):
        """Test loading valid rules from YAML."""
        yaml_content = """
rules:
  - id: test-1
    name: Test Rule
    category: test
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value: test
"""
        path = self._write_rules_file(yaml_content)
        engine = RuleEngine()
        rules = engine.load_rules(path)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].id, "test-1")
        self.assertEqual(rules[0].name, "Test Rule")
        self.assertTrue(rules[0].enabled)

    def test_load_multiple_rules(self):
        """Test loading multiple rules."""
        yaml_content = """
rules:
  - id: rule-1
    name: Rule One
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value: hello
  - id: rule-2
    name: Rule Two
    priority: low
    severity: warn
    enabled: true
    conditions:
      - type: keyword
        value: world
"""
        path = self._write_rules_file(yaml_content)
        engine = RuleEngine()
        rules = engine.load_rules(path)
        self.assertEqual(len(rules), 2)

    def test_rules_sorted_by_priority(self):
        """Test that rules are sorted by priority after loading."""
        yaml_content = """
rules:
  - id: low-rule
    name: Low Priority
    priority: low
    severity: log
    enabled: true
    conditions:
      - type: keyword
        value: a
  - id: high-rule
    name: High Priority
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value: b
  - id: med-rule
    name: Medium Priority
    priority: medium
    severity: warn
    enabled: true
    conditions:
      - type: keyword
        value: c
"""
        path = self._write_rules_file(yaml_content)
        engine = RuleEngine()
        rules = engine.load_rules(path)
        self.assertEqual(rules[0].id, "high-rule")
        self.assertEqual(rules[1].id, "med-rule")
        self.assertEqual(rules[2].id, "low-rule")

    def test_disabled_rules_loaded(self):
        """Test that disabled rules are still loaded."""
        yaml_content = """
rules:
  - id: disabled-rule
    name: Disabled
    enabled: false
    conditions:
      - type: keyword
        value: test
"""
        path = self._write_rules_file(yaml_content)
        engine = RuleEngine()
        rules = engine.load_rules(path)
        self.assertEqual(len(rules), 1)
        self.assertFalse(rules[0].enabled)

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file raises error."""
        engine = RuleEngine()
        with self.assertRaises(FileNotFoundError):
            engine.load_rules("/nonexistent/path.yaml")

    def test_load_json_rules(self):
        """Test loading rules from JSON file."""
        rules_data = {
            "rules": [
                {
                    "id": "json-rule",
                    "name": "JSON Rule",
                    "priority": "high",
                    "severity": "block",
                    "enabled": True,
                    "conditions": [
                        {"type": "keyword", "value": "test"}
                    ],
                }
            ]
        }
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(rules_data, f)
        f.flush()
        f.close()
        self.addCleanup(os.unlink, f.name)

        engine = RuleEngine()
        rules = engine.load_rules(f.name)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].id, "json-rule")


class TestCheckMessage(unittest.TestCase):
    """Tests for checking messages against rules."""

    def _make_engine(self, rules: list[Rule]) -> RuleEngine:
        """Create an engine with the given rules."""
        engine = RuleEngine()
        engine.rules = rules
        return engine

    def test_keyword_match_negate_true(self):
        """Test negated keyword condition detects forbidden word."""
        rule = Rule(
            id="no-bad-word",
            name="No Bad Word",
            severity="block",
            conditions=[
                Condition(type="keyword", value="badword", negate=True),
            ],
        )
        engine = self._make_engine([rule])
        result = engine.check_message("This contains a badword here")
        self.assertTrue(any(r.matched for r in result.rule_results))
        self.assertFalse(result.passed)

    def test_keyword_match_negate_false(self):
        """Test normal keyword condition requires word presence."""
        rule = Rule(
            id="require-hello",
            name="Require Hello",
            severity="warn",
            conditions=[
                Condition(type="keyword", value="hello"),
            ],
        )
        engine = self._make_engine([rule])
        result = engine.check_message("This message has no greeting")
        self.assertTrue(any(r.matched for r in result.rule_results))

    def test_keyword_pass(self):
        """Test keyword condition passes when word is present."""
        rule = Rule(
            id="require-hello",
            name="Require Hello",
            severity="warn",
            conditions=[
                Condition(type="keyword", value="hello"),
            ],
        )
        engine = self._make_engine([rule])
        result = engine.check_message("Hello, how can I help you?")
        self.assertFalse(any(r.matched for r in result.rule_results))
        self.assertTrue(result.passed)

    def test_regex_match(self):
        """Test regex condition detects SSN pattern."""
        rule = Rule(
            id="no-ssn",
            name="No SSN",
            severity="block",
            conditions=[
                Condition(type="regex", value=r"\d{3}-\d{2}-\d{4}", negate=True),
            ],
        )
        engine = self._make_engine([rule])
        result = engine.check_message("My SSN is 123-45-6789")
        self.assertFalse(result.passed)

    def test_regex_no_match(self):
        """Test regex condition passes when pattern not found."""
        rule = Rule(
            id="no-ssn",
            name="No SSN",
            severity="block",
            conditions=[
                Condition(type="regex", value=r"\d{3}-\d{2}-\d{4}", negate=True),
            ],
        )
        engine = self._make_engine([rule])
        result = engine.check_message("This is a safe message")
        self.assertTrue(result.passed)

    def test_length_condition(self):
        """Test length condition detects overly long messages."""
        rule = Rule(
            id="max-length",
            name="Max Length",
            severity="warn",
            conditions=[
                Condition(type="length", value=100, negate=True),
            ],
        )
        engine = self._make_engine([rule])
        long_message = "x" * 200
        result = engine.check_message(long_message)
        self.assertTrue(any(r.matched for r in result.rule_results))

    def test_length_condition_pass(self):
        """Test length condition passes for short messages."""
        rule = Rule(
            id="max-length",
            name="Max Length",
            severity="warn",
            conditions=[
                Condition(type="length", value=100, negate=True),
            ],
        )
        engine = self._make_engine([rule])
        result = engine.check_message("Short message")
        self.assertTrue(result.passed)

    def test_custom_condition_contains_any(self):
        """Test custom condition with contains_any."""
        rule = Rule(
            id="no-slang",
            name="No Slang",
            severity="warn",
            conditions=[
                Condition(type="custom", value="contains_any:lol,omg,bruh", negate=True),
            ],
        )
        engine = self._make_engine([rule])
        result = engine.check_message("That's omg so funny")
        self.assertTrue(any(r.matched for r in result.rule_results))

    def test_custom_condition_starts_with(self):
        """Test custom condition with starts_with."""
        rule = Rule(
            id="must-start",
            name="Must Start With",
            severity="log",
            conditions=[
                Condition(type="custom", value="starts_with:Hello"),
            ],
        )
        engine = self._make_engine([rule])
        result = engine.check_message("Hello, welcome!")
        self.assertTrue(result.passed)

    def test_disabled_rule_skipped(self):
        """Test that disabled rules are not evaluated."""
        rule = Rule(
            id="disabled",
            name="Disabled Rule",
            severity="block",
            enabled=False,
            conditions=[
                Condition(type="keyword", value="badword", negate=True),
            ],
        )
        engine = self._make_engine([rule])
        result = engine.check_message("This has a badword")
        self.assertTrue(result.passed)

    def test_compliance_score_calculation(self):
        """Test compliance score is calculated correctly."""
        rule = Rule(
            id="block-rule",
            name="Block Rule",
            severity="block",
            conditions=[
                Condition(type="keyword", value="forbidden", negate=True),
            ],
        )
        engine = self._make_engine([rule])
        result = engine.check_message("This contains forbidden content")
        self.assertEqual(result.score, 80.0)  # 100 - 20 for block violation
        self.assertFalse(result.passed)

    def test_multiple_violations_score(self):
        """Test score with multiple violations."""
        rules = [
            Rule(
                id="block-1",
                name="Block 1",
                severity="block",
                conditions=[Condition(type="keyword", value="bad1", negate=True)],
            ),
            Rule(
                id="warn-1",
                name="Warn 1",
                severity="warn",
                conditions=[Condition(type="keyword", value="bad2", negate=True)],
            ),
        ]
        engine = self._make_engine(rules)
        result = engine.check_message("bad1 and bad2 are here")
        self.assertEqual(result.score, 70.0)  # 100 - 20 (block) - 10 (warn)

    def test_score_floor(self):
        """Test score cannot go below 0."""
        rules = [
            Rule(
                id=f"block-{i}",
                name=f"Block {i}",
                severity="block",
                conditions=[Condition(type="keyword", value=f"word{i}", negate=True)],
            )
            for i in range(10)
        ]
        engine = self._make_engine(rules)
        message = " ".join(f"word{i}" for i in range(10))
        result = engine.check_message(message)
        self.assertGreaterEqual(result.score, 0.0)

    def test_empty_message(self):
        """Test checking an empty message."""
        rule = Rule(
            id="require-hello",
            name="Require Hello",
            severity="warn",
            conditions=[Condition(type="keyword", value="hello")],
        )
        engine = self._make_engine([rule])
        result = engine.check_message("")
        self.assertTrue(any(r.matched for r in result.rule_results))

    def test_no_conditions(self):
        """Test rule with no conditions."""
        rule = Rule(id="empty", name="Empty Rule")
        engine = self._make_engine([rule])
        result = engine.check_message("Any message")
        self.assertTrue(result.passed)


class TestCheckConversation(unittest.TestCase):
    """Tests for checking conversations against rules."""

    def _make_engine(self, rules: list[Rule]) -> RuleEngine:
        """Create an engine with the given rules."""
        engine = RuleEngine()
        engine.rules = rules
        return engine

    def test_check_conversation_object(self):
        """Test checking a Conversation object."""
        conv = Conversation()
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")

        rule = Rule(
            id="no-bad",
            name="No Bad",
            severity="block",
            conditions=[Condition(type="keyword", value="bad", negate=True)],
        )
        engine = self._make_engine([rule])
        results = engine.check_conversation(conv)
        self.assertEqual(len(results), 1)  # Only assistant messages checked
        self.assertTrue(results[0].passed)

    def test_check_conversation_dict(self):
        """Test checking a conversation dict."""
        data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        }
        rule = Rule(
            id="no-bad",
            name="No Bad",
            severity="block",
            conditions=[Condition(type="keyword", value="bad", negate=True)],
        )
        engine = self._make_engine([rule])
        results = engine.check_conversation(data)
        self.assertEqual(len(results), 1)

    def test_check_conversation_file(self):
        """Test checking a conversation from a JSON file."""
        conv_data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        }
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(conv_data, f)
        f.flush()
        f.close()
        self.addCleanup(os.unlink, f.name)

        rule = Rule(
            id="no-bad",
            name="No Bad",
            severity="block",
            conditions=[Condition(type="keyword", value="bad", negate=True)],
        )
        engine = self._make_engine([rule])
        results = engine.check_conversation(f.name)
        self.assertEqual(len(results), 1)

    def test_only_assistant_messages_checked(self):
        """Test that only assistant messages are checked."""
        conv = Conversation()
        conv.add_message("system", "You are helpful.")
        conv.add_message("user", "badword here")
        conv.add_message("assistant", "Clean response")

        rule = Rule(
            id="no-bad",
            name="No Bad",
            severity="block",
            conditions=[Condition(type="keyword", value="badword", negate=True)],
        )
        engine = self._make_engine([rule])
        results = engine.check_conversation(conv)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].passed)

    def test_multiple_assistant_messages(self):
        """Test checking multiple assistant messages."""
        conv = Conversation()
        conv.add_message("user", "Hi")
        conv.add_message("assistant", "Clean response one")
        conv.add_message("user", "Hi again")
        conv.add_message("assistant", "Clean response two")

        rule = Rule(
            id="no-bad",
            name="No Bad",
            severity="block",
            conditions=[Condition(type="keyword", value="bad", negate=True)],
        )
        engine = self._make_engine([rule])
        results = engine.check_conversation(conv)
        self.assertEqual(len(results), 2)


class TestDetectConflicts(unittest.TestCase):
    """Tests for rule conflict detection."""

    def test_detect_conflict(self):
        """Test detecting conflicting rules."""
        rules = [
            Rule(
                id="require-x",
                name="Require X",
                category="test",
                conditions=[Condition(type="keyword", value="x")],
            ),
            Rule(
                id="forbid-x",
                name="Forbid X",
                category="test",
                conditions=[Condition(type="keyword", value="x", negate=True)],
            ),
        ]
        engine = RuleEngine()
        conflicts = engine.detect_conflicts(rules)
        self.assertEqual(len(conflicts), 1)
        self.assertIn("require-x", conflicts[0]["rule_a"])
        self.assertIn("forbid-x", conflicts[0]["rule_b"])

    def test_no_conflict_different_categories(self):
        """Test no conflict detected for different categories."""
        rules = [
            Rule(
                id="a",
                name="A",
                category="cat1",
                conditions=[Condition(type="keyword", value="x")],
            ),
            Rule(
                id="b",
                name="B",
                category="cat2",
                conditions=[Condition(type="keyword", value="x", negate=True)],
            ),
        ]
        engine = RuleEngine()
        conflicts = engine.detect_conflicts(rules)
        self.assertEqual(len(conflicts), 0)

    def test_no_conflict_same_direction(self):
        """Test no conflict when both rules have same negate direction."""
        rules = [
            Rule(
                id="a",
                name="A",
                category="test",
                conditions=[Condition(type="keyword", value="x", negate=True)],
            ),
            Rule(
                id="b",
                name="B",
                category="test",
                conditions=[Condition(type="keyword", value="x", negate=True)],
            ),
        ]
        engine = RuleEngine()
        conflicts = engine.detect_conflicts(rules)
        self.assertEqual(len(conflicts), 0)


if __name__ == "__main__":
    unittest.main()
