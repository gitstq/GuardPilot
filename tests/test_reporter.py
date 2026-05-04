"""Tests for GuardPilot report generator."""

import unittest

from guardpilot.models import (
    ComplianceResult,
    Condition,
    Rule,
    RuleResult,
)
from guardpilot.reporter import Reporter


class TestReporterInit(unittest.TestCase):
    """Tests for Reporter initialization."""

    def test_init(self):
        """Test reporter initializes without error."""
        reporter = Reporter()
        self.assertIsNotNone(reporter.timestamp)


class TestGenerateJSON(unittest.TestCase):
    """Tests for JSON report generation."""

    def test_json_report_pass(self):
        """Test JSON report for a passing result."""
        result = ComplianceResult(
            message="Hello world",
            score=100.0,
            passed=True,
        )
        reporter = Reporter()
        output = reporter.generate_json(result)
        import json
        data = json.loads(output)
        self.assertEqual(data["compliance"]["score"], 100.0)
        self.assertTrue(data["compliance"]["passed"])
        self.assertEqual(len(data["violations"]), 0)

    def test_json_report_with_violations(self):
        """Test JSON report with violations."""
        rule = Rule(id="r1", name="Bad Rule", severity="block")
        violation = RuleResult(
            rule=rule,
            matched=True,
            details="Violation found",
            severity="block",
        )
        result = ComplianceResult(
            message="Bad message",
            score=80.0,
            passed=False,
            violations=[violation],
        )
        reporter = Reporter()
        output = reporter.generate_json(result)
        import json
        data = json.loads(output)
        self.assertEqual(len(data["violations"]), 1)
        self.assertEqual(data["violations"][0]["rule_id"], "r1")

    def test_json_conversation_report(self):
        """Test JSON conversation report."""
        results = [
            ComplianceResult(message="msg1", score=90.0, passed=True),
            ComplianceResult(message="msg2", score=70.0, passed=False),
        ]
        reporter = Reporter()
        output = reporter.generate_json_conversation(results)
        import json
        data = json.loads(output)
        self.assertEqual(data["summary"]["total_messages"], 2)
        self.assertFalse(data["summary"]["all_passed"])


class TestGenerateMarkdown(unittest.TestCase):
    """Tests for Markdown report generation."""

    def test_markdown_report_pass(self):
        """Test Markdown report for a passing result."""
        result = ComplianceResult(
            message="Hello world",
            score=100.0,
            passed=True,
        )
        reporter = Reporter()
        output = reporter.generate_markdown(result)
        self.assertIn("# GuardPilot Compliance Report", output)
        self.assertIn("PASS", output)
        self.assertIn("100", output)

    def test_markdown_report_fail(self):
        """Test Markdown report for a failing result."""
        rule = Rule(id="r1", name="Bad Rule", severity="block")
        violation = RuleResult(
            rule=rule,
            matched=True,
            details="Violation",
            severity="block",
        )
        result = ComplianceResult(
            message="Bad message",
            score=80.0,
            passed=False,
            violations=[violation],
        )
        reporter = Reporter()
        output = reporter.generate_markdown(result)
        self.assertIn("FAIL", output)
        self.assertIn("Violations", output)

    def test_markdown_conversation_report(self):
        """Test Markdown conversation report."""
        results = [
            ComplianceResult(message="msg1", score=100.0, passed=True),
        ]
        reporter = Reporter()
        output = reporter.generate_markdown_conversation(results)
        self.assertIn("# GuardPilot Conversation Compliance Report", output)
        self.assertIn("Message 1", output)


class TestGenerateHTML(unittest.TestCase):
    """Tests for HTML report generation."""

    def test_html_report_structure(self):
        """Test HTML report contains expected structure."""
        result = ComplianceResult(
            message="Hello world",
            score=95.0,
            passed=True,
        )
        reporter = Reporter()
        output = reporter.generate_html(result)
        self.assertIn("<!DOCTYPE html>", output)
        self.assertIn("<html", output)
        self.assertIn("</html>", output)
        self.assertIn("GuardPilot Compliance Report", output)
        self.assertIn("95", output)

    def test_html_report_dark_theme(self):
        """Test HTML report uses dark theme colors."""
        result = ComplianceResult(
            message="Test",
            score=100.0,
            passed=True,
        )
        reporter = Reporter()
        output = reporter.generate_html(result)
        self.assertIn("#0f172a", output)  # Dark background
        self.assertIn("#1e293b", output)  # Card background

    def test_html_report_with_violations(self):
        """Test HTML report displays violations."""
        rule = Rule(id="r1", name="Bad Rule", severity="block")
        violation = RuleResult(
            rule=rule,
            matched=True,
            details="Violation found",
            severity="block",
        )
        result = ComplianceResult(
            message="Bad message",
            score=80.0,
            passed=False,
            violations=[violation],
        )
        reporter = Reporter()
        output = reporter.generate_html(result)
        self.assertIn("Bad Rule", output)
        self.assertIn("BLOCK", output)
        self.assertIn("FAILED", output)

    def test_html_conversation_report(self):
        """Test HTML conversation report."""
        results = [
            ComplianceResult(message="msg1", score=90.0, passed=True),
            ComplianceResult(message="msg2", score=70.0, passed=False),
        ]
        reporter = Reporter()
        output = reporter.generate_html_conversation(results)
        self.assertIn("<!DOCTYPE html>", output)
        self.assertIn("Message 1", output)
        self.assertIn("Message 2", output)

    def test_html_escaping(self):
        """Test HTML special characters are escaped."""
        result = ComplianceResult(
            message="<script>alert('xss')</script>",
            score=100.0,
            passed=True,
        )
        reporter = Reporter()
        output = reporter.generate_html(result)
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)


class TestGenerateSummary(unittest.TestCase):
    """Tests for terminal summary generation."""

    def test_summary_pass(self):
        """Test summary for a passing result."""
        result = ComplianceResult(
            message="Hello world",
            score=100.0,
            passed=True,
        )
        reporter = Reporter()
        output = reporter.generate_summary(result)
        self.assertIn("GuardPilot Compliance Check", output)
        self.assertIn("100", output)
        self.assertIn("PASSED", output)

    def test_summary_fail(self):
        """Test summary for a failing result."""
        rule = Rule(id="r1", name="Bad Rule", severity="block")
        violation = RuleResult(
            rule=rule,
            matched=True,
            details="Violation",
            severity="block",
        )
        result = ComplianceResult(
            message="Bad message",
            score=80.0,
            passed=False,
            violations=[violation],
        )
        reporter = Reporter()
        output = reporter.generate_summary(result)
        self.assertIn("FAILED", output)
        self.assertIn("Violations:", output)
        self.assertIn("Bad Rule", output)

    def test_summary_with_warnings(self):
        """Test summary includes warnings."""
        rule = Rule(id="r1", name="Warn Rule", severity="warn")
        warning = RuleResult(
            rule=rule,
            matched=True,
            details="Warning",
            severity="warn",
        )
        result = ComplianceResult(
            message="Message",
            score=90.0,
            passed=True,
            warnings=[warning],
        )
        reporter = Reporter()
        output = reporter.generate_summary(result)
        self.assertIn("Warnings:", output)

    def test_summary_conversation(self):
        """Test conversation summary."""
        results = [
            ComplianceResult(message="msg1", score=100.0, passed=True),
            ComplianceResult(message="msg2", score=80.0, passed=False),
        ]
        reporter = Reporter()
        output = reporter.generate_summary_conversation(results)
        self.assertIn("Conversation Check", output)
        self.assertIn("Messages checked: 2", output)


class TestEscapeHtml(unittest.TestCase):
    """Tests for HTML escaping utility."""

    def test_escape_ampersand(self):
        """Test ampersand is escaped."""
        self.assertEqual(Reporter._escape_html("a&b"), "a&amp;b")

    def test_escape_angle_brackets(self):
        """Test angle brackets are escaped."""
        self.assertEqual(Reporter._escape_html("<b>"), "&lt;b&gt;")

    def test_escape_quotes(self):
        """Test quotes are escaped."""
        self.assertEqual(Reporter._escape_html('"hi"'), "&quot;hi&quot;")

    def test_no_escape_needed(self):
        """Test normal text is unchanged."""
        self.assertEqual(Reporter._escape_html("hello"), "hello")


if __name__ == "__main__":
    unittest.main()
