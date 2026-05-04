"""Tests for GuardPilot data models."""

import unittest
from dataclasses import fields

from guardpilot.models import (
    ComplianceResult,
    Condition,
    Conversation,
    Message,
    Rule,
    RuleResult,
)


class TestCondition(unittest.TestCase):
    """Tests for the Condition dataclass."""

    def test_default_values(self):
        """Test Condition default field values."""
        cond = Condition()
        self.assertEqual(cond.type, "keyword")
        self.assertEqual(cond.value, "")
        self.assertFalse(cond.negate)

    def test_custom_values(self):
        """Test Condition with custom values."""
        cond = Condition(type="regex", value="\\d+", negate=True)
        self.assertEqual(cond.type, "regex")
        self.assertEqual(cond.value, "\\d+")
        self.assertTrue(cond.negate)


class TestRule(unittest.TestCase):
    """Tests for the Rule dataclass."""

    def test_default_values(self):
        """Test Rule default field values."""
        rule = Rule()
        self.assertEqual(rule.id, "")
        self.assertEqual(rule.name, "")
        self.assertEqual(rule.category, "general")
        self.assertEqual(rule.priority, "medium")
        self.assertEqual(rule.severity, "warn")
        self.assertTrue(rule.enabled)
        self.assertEqual(rule.conditions, [])

    def test_full_rule(self):
        """Test Rule with all fields populated."""
        conditions = [
            Condition(type="keyword", value="hello"),
            Condition(type="regex", value="\\d+"),
        ]
        rule = Rule(
            id="test-001",
            name="Test Rule",
            description="A test rule",
            category="content_safety",
            priority="high",
            conditions=conditions,
            severity="block",
            enabled=True,
        )
        self.assertEqual(rule.id, "test-001")
        self.assertEqual(rule.name, "Test Rule")
        self.assertEqual(len(rule.conditions), 2)
        self.assertEqual(rule.priority, "high")
        self.assertEqual(rule.severity, "block")


class TestRuleResult(unittest.TestCase):
    """Tests for the RuleResult dataclass."""

    def test_default_values(self):
        """Test RuleResult default field values."""
        result = RuleResult()
        self.assertFalse(result.matched)
        self.assertEqual(result.details, "")
        self.assertEqual(result.severity, "warn")

    def test_with_rule(self):
        """Test RuleResult with a rule attached."""
        rule = Rule(id="r1", name="Test")
        result = RuleResult(rule=rule, matched=True, details="Matched", severity="block")
        self.assertTrue(result.matched)
        self.assertEqual(result.rule.id, "r1")
        self.assertEqual(result.details, "Matched")


class TestComplianceResult(unittest.TestCase):
    """Tests for the ComplianceResult dataclass."""

    def test_default_values(self):
        """Test ComplianceResult default field values."""
        result = ComplianceResult()
        self.assertEqual(result.message, "")
        self.assertEqual(result.score, 100.0)
        self.assertTrue(result.passed)
        self.assertEqual(result.violations, [])
        self.assertEqual(result.warnings, [])

    def test_with_violations(self):
        """Test ComplianceResult with violations."""
        rule = Rule(id="r1", name="Test", severity="block")
        violation = RuleResult(rule=rule, matched=True, details="Violation", severity="block")
        result = ComplianceResult(
            message="test message",
            violations=[violation],
            passed=False,
            score=80.0,
        )
        self.assertFalse(result.passed)
        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.score, 80.0)


class TestMessage(unittest.TestCase):
    """Tests for the Message dataclass."""

    def test_default_values(self):
        """Test Message default field values."""
        msg = Message()
        self.assertEqual(msg.role, "assistant")
        self.assertEqual(msg.content, "")
        self.assertIsNone(msg.timestamp)

    def test_custom_message(self):
        """Test Message with custom values."""
        msg = Message(role="user", content="Hello", timestamp="2025-01-01T00:00:00Z")
        self.assertEqual(msg.role, "user")
        self.assertEqual(msg.content, "Hello")
        self.assertEqual(msg.timestamp, "2025-01-01T00:00:00Z")


class TestConversation(unittest.TestCase):
    """Tests for the Conversation dataclass."""

    def test_empty_conversation(self):
        """Test empty conversation."""
        conv = Conversation()
        self.assertEqual(conv.messages, [])
        self.assertEqual(conv.metadata, {})

    def test_add_message(self):
        """Test adding messages to a conversation."""
        conv = Conversation()
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")
        self.assertEqual(len(conv.messages), 2)

    def test_get_assistant_messages(self):
        """Test filtering assistant messages."""
        conv = Conversation()
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")
        conv.add_message("user", "How are you?")
        conv.add_message("assistant", "I'm fine!")
        assistant_msgs = conv.get_assistant_messages()
        self.assertEqual(len(assistant_msgs), 2)

    def test_to_dict(self):
        """Test conversation serialization to dict."""
        conv = Conversation()
        conv.add_message("user", "Hello")
        d = conv.to_dict()
        self.assertIn("messages", d)
        self.assertEqual(len(d["messages"]), 1)
        self.assertEqual(d["messages"][0]["role"], "user")

    def test_from_dict(self):
        """Test conversation deserialization from dict."""
        data = {
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": "2025-01-01T00:00:00Z"},
                {"role": "assistant", "content": "Hi!", "timestamp": "2025-01-01T00:00:01Z"},
            ],
            "metadata": {"id": "conv-1"},
        }
        conv = Conversation.from_dict(data)
        self.assertEqual(len(conv.messages), 2)
        self.assertEqual(conv.metadata["id"], "conv-1")
        self.assertEqual(conv.messages[0].role, "user")

    def test_roundtrip(self):
        """Test dict serialization roundtrip."""
        conv = Conversation()
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")
        conv.metadata["test"] = True

        d = conv.to_dict()
        conv2 = Conversation.from_dict(d)

        self.assertEqual(len(conv2.messages), 2)
        self.assertEqual(conv2.messages[0].content, "Hello")
        self.assertEqual(conv2.metadata["test"], True)


if __name__ == "__main__":
    unittest.main()
