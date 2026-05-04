"""Report generator for GuardPilot.

Generates compliance reports in multiple formats: JSON, Markdown,
HTML (with dark theme), and terminal summary with colored output.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from .models import ComplianceResult, Conversation
from .utils import (
    Colors,
    bold_text,
    colored_text,
    format_timestamp,
)


class Reporter:
    """Generates compliance reports in various formats.

    Supports JSON, Markdown, HTML (standalone with dark theme),
    and colored terminal output.
    """

    def __init__(self) -> None:
        """Initialize the reporter."""
        self.timestamp = format_timestamp()

    def generate_json(self, result: ComplianceResult) -> str:
        """Generate a JSON format compliance report.

        Args:
            result: The compliance result to report.

        Returns:
            JSON-formatted string.
        """
        report: dict[str, Any] = {
            "guardpilot_version": "1.0.0",
            "timestamp": self.timestamp,
            "compliance": {
                "score": result.score,
                "passed": result.passed,
                "message_length": len(result.message),
                "message_preview": result.message[:200] + ("..." if len(result.message) > 200 else ""),
            },
            "violations": [
                {
                    "rule_id": vr.rule.id,
                    "rule_name": vr.rule.name,
                    "severity": vr.severity,
                    "details": vr.details,
                }
                for vr in result.violations
            ],
            "warnings": [
                {
                    "rule_id": wr.rule.id,
                    "rule_name": wr.rule.name,
                    "severity": wr.severity,
                    "details": wr.details,
                }
                for wr in result.warnings
            ],
            "all_results": [
                {
                    "rule_id": rr.rule.id,
                    "rule_name": rr.rule.name,
                    "matched": rr.matched,
                    "severity": rr.severity,
                    "details": rr.details,
                }
                for rr in result.rule_results
            ],
        }

        return json.dumps(report, indent=2, ensure_ascii=False)

    def generate_json_conversation(
        self, results: list[ComplianceResult]
    ) -> str:
        """Generate a JSON report for a full conversation check.

        Args:
            results: List of compliance results for each message.

        Returns:
            JSON-formatted string.
        """
        total_score = sum(r.score for r in results) / len(results) if results else 100.0
        all_passed = all(r.passed for r in results)

        report: dict[str, Any] = {
            "guardpilot_version": "1.0.0",
            "timestamp": self.timestamp,
            "summary": {
                "total_messages": len(results),
                "average_score": round(total_score, 1),
                "all_passed": all_passed,
                "total_violations": sum(len(r.violations) for r in results),
                "total_warnings": sum(len(r.warnings) for r in results),
            },
            "messages": [
                {
                    "index": i,
                    "score": r.score,
                    "passed": r.passed,
                    "message_preview": r.message[:200] + ("..." if len(r.message) > 200 else ""),
                    "violations": [
                        {
                            "rule_id": vr.rule.id,
                            "rule_name": vr.rule.name,
                            "severity": vr.severity,
                            "details": vr.details,
                        }
                        for vr in r.violations
                    ],
                    "warnings": [
                        {
                            "rule_id": wr.rule.id,
                            "rule_name": wr.rule.name,
                            "severity": wr.severity,
                            "details": wr.details,
                        }
                        for wr in r.warnings
                    ],
                }
                for i, r in enumerate(results)
            ],
        }

        return json.dumps(report, indent=2, ensure_ascii=False)

    def generate_markdown(self, result: ComplianceResult) -> str:
        """Generate a Markdown format compliance report.

        Args:
            result: The compliance result to report.

        Returns:
            Markdown-formatted string.
        """
        status_emoji = "PASS" if result.passed else "FAIL"
        score_emoji = "A" if result.score >= 90 else "B" if result.score >= 70 else "C" if result.score >= 50 else "D"

        lines: list[str] = []
        lines.append(f"# GuardPilot Compliance Report")
        lines.append(f"")
        lines.append(f"**Generated:** {self.timestamp}")
        lines.append(f"**Status:** {status_emoji}")
        lines.append(f"**Score:** {result.score}/100 ({score_emoji})")
        lines.append(f"**Message Length:** {len(result.message)} characters")
        lines.append(f"")

        # Score bar
        filled = int(result.score / 5)
        bar = "[" + "#" * filled + "-" * (20 - filled) + "]"
        lines.append(f"**Compliance Bar:** {bar}")
        lines.append(f"")

        # Violations
        if result.violations:
            lines.append(f"## Violations")
            lines.append(f"")
            for i, v in enumerate(result.violations, 1):
                lines.append(f"{i}. **[{v.severity.upper()}]** {v.rule.name} ({v.rule.id})")
                lines.append(f"   - {v.details}")
                lines.append(f"")
        else:
            lines.append(f"## Violations")
            lines.append(f"")
            lines.append(f"No violations found.")
            lines.append(f"")

        # Warnings
        if result.warnings:
            lines.append(f"## Warnings")
            lines.append(f"")
            for i, w in enumerate(result.warnings, 1):
                lines.append(f"{i}. **[{w.severity.upper()}]** {w.rule.name} ({w.rule.id})")
                lines.append(f"   - {w.details}")
                lines.append(f"")
        else:
            lines.append(f"## Warnings")
            lines.append(f"")
            lines.append(f"No warnings found.")
            lines.append(f"")

        # All Results
        lines.append(f"## Detailed Results")
        lines.append(f"")
        lines.append(f"| Rule | Status | Severity | Details |")
        lines.append(f"|------|--------|----------|---------|")
        for rr in result.rule_results:
            status = "MATCHED" if rr.matched else "PASSED"
            lines.append(f"| {rr.rule.name} | {status} | {rr.severity} | {rr.details[:60]} |")
        lines.append(f"")

        # Message Preview
        lines.append(f"## Message Preview")
        lines.append(f"")
        lines.append(f"```")
        preview = result.message[:500]
        if len(result.message) > 500:
            preview += "..."
        lines.append(preview)
        lines.append(f"```")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"*Generated by GuardPilot v1.0.0*")

        return "\n".join(lines)

    def generate_markdown_conversation(
        self, results: list[ComplianceResult]
    ) -> str:
        """Generate a Markdown report for a full conversation check.

        Args:
            results: List of compliance results for each message.

        Returns:
            Markdown-formatted string.
        """
        total_score = sum(r.score for r in results) / len(results) if results else 100.0
        all_passed = all(r.passed for r in results)

        lines: list[str] = []
        lines.append(f"# GuardPilot Conversation Compliance Report")
        lines.append(f"")
        lines.append(f"**Generated:** {self.timestamp}")
        lines.append(f"**Total Messages:** {len(results)}")
        lines.append(f"**Average Score:** {round(total_score, 1)}/100")
        lines.append(f"**Overall Status:** {'PASS' if all_passed else 'FAIL'}")
        lines.append(f"**Total Violations:** {sum(len(r.violations) for r in results)}")
        lines.append(f"**Total Warnings:** {sum(len(r.warnings) for r in results)}")
        lines.append(f"")

        for i, result in enumerate(results, 1):
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"## Message {i}")
            lines.append(f"")
            lines.append(f"**Score:** {result.score}/100 | **Status:** {status}")
            lines.append(f"")
            lines.append(f"**Preview:** {result.message[:150]}{'...' if len(result.message) > 150 else ''}")
            lines.append(f"")

            if result.violations:
                for v in result.violations:
                    lines.append(f"- **[VIOLATION]** {v.rule.name}: {v.details}")
            if result.warnings:
                for w in result.warnings:
                    lines.append(f"- **[WARNING]** {w.rule.name}: {w.details}")
            if not result.violations and not result.warnings:
                lines.append(f"- No issues found.")
            lines.append(f"")

        lines.append(f"---")
        lines.append(f"*Generated by GuardPilot v1.0.0*")

        return "\n".join(lines)

    def generate_html(self, result: ComplianceResult) -> str:
        """Generate a standalone HTML compliance report with dark theme.

        Args:
            result: The compliance result to report.

        Returns:
            Complete HTML document string with inline CSS.
        """
        score_color = (
            "#4ade80" if result.score >= 80
            else "#facc15" if result.score >= 60
            else "#f87171"
        )
        status_text = "PASSED" if result.passed else "FAILED"
        status_color = "#4ade80" if result.passed else "#f87171"

        violations_html = ""
        for v in result.violations:
            violations_html += f"""
            <div class="violation-item">
                <span class="severity-badge severity-block">BLOCK</span>
                <div class="violation-content">
                    <strong>{self._escape_html(v.rule.name)}</strong>
                    <span class="rule-id">{self._escape_html(v.rule.id)}</span>
                    <p>{self._escape_html(v.details)}</p>
                </div>
            </div>"""

        warnings_html = ""
        for w in result.warnings:
            warnings_html += f"""
            <div class="warning-item">
                <span class="severity-badge severity-warn">WARN</span>
                <div class="warning-content">
                    <strong>{self._escape_html(w.rule.name)}</strong>
                    <span class="rule-id">{self._escape_html(w.rule.id)}</span>
                    <p>{self._escape_html(w.details)}</p>
                </div>
            </div>"""

        results_rows = ""
        for rr in result.rule_results:
            status = "matched" if rr.matched else "passed"
            results_rows += f"""
            <tr class="result-row {status}">
                <td>{self._escape_html(rr.rule.name)}</td>
                <td><span class="status-badge {status}">{status.upper()}</span></td>
                <td>{rr.severity}</td>
                <td>{self._escape_html(rr.details[:80])}</td>
            </tr>"""

        preview = self._escape_html(result.message[:1000])
        if len(result.message) > 1000:
            preview += "..."

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GuardPilot Compliance Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            line-height: 1.6;
            min-height: 100vh;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid #1e293b;
        }}
        .header h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 0.5rem;
        }}
        .header .subtitle {{
            color: #94a3b8;
            font-size: 0.9rem;
        }}
        .score-card {{
            background: #1e293b;
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            margin-bottom: 2rem;
            border: 1px solid #334155;
        }}
        .score-value {{
            font-size: 4rem;
            font-weight: 800;
            color: {score_color};
            line-height: 1;
        }}
        .score-label {{
            color: #94a3b8;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }}
        .status-badge-large {{
            display: inline-block;
            padding: 0.4rem 1.2rem;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.85rem;
            margin-top: 1rem;
            background: {status_color}20;
            color: {status_color};
            border: 1px solid {status_color}40;
        }}
        .score-bar-container {{
            background: #334155;
            border-radius: 8px;
            height: 12px;
            margin-top: 1rem;
            overflow: hidden;
        }}
        .score-bar {{
            height: 100%;
            border-radius: 8px;
            background: {score_color};
            transition: width 0.3s ease;
        }}
        .section {{
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid #334155;
        }}
        .section h2 {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #f8fafc;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #334155;
        }}
        .violation-item, .warning-item {{
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 8px;
            background: #0f172a;
        }}
        .severity-badge {{
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            white-space: nowrap;
        }}
        .severity-block {{
            background: #f8717120;
            color: #f87171;
            border: 1px solid #f8717140;
        }}
        .severity-warn {{
            background: #facc1520;
            color: #facc15;
            border: 1px solid #facc1540;
        }}
        .violation-content, .warning-content {{
            flex: 1;
        }}
        .violation-content strong, .warning-content strong {{
            color: #f8fafc;
            font-size: 0.9rem;
        }}
        .rule-id {{
            color: #64748b;
            font-size: 0.8rem;
            margin-left: 0.5rem;
        }}
        .violation-content p, .warning-content p {{
            color: #94a3b8;
            font-size: 0.85rem;
            margin-top: 0.25rem;
        }}
        .no-issues {{
            color: #64748b;
            font-style: italic;
            text-align: center;
            padding: 1rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            text-align: left;
            padding: 0.6rem 0.75rem;
            color: #94a3b8;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid #334155;
        }}
        td {{
            padding: 0.6rem 0.75rem;
            font-size: 0.85rem;
            border-bottom: 1px solid #1e293b;
        }}
        .result-row.passed td {{ color: #94a3b8; }}
        .result-row.matched td {{ color: #e2e8f0; background: #f8717108; }}
        .status-badge {{
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
        }}
        .status-badge.passed {{ background: #4ade8020; color: #4ade80; }}
        .status-badge.matched {{ background: #f8717120; color: #f87171; }}
        .message-preview {{
            background: #0f172a;
            border-radius: 8px;
            padding: 1rem;
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 0.85rem;
            color: #cbd5e1;
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 300px;
            overflow-y: auto;
        }}
        .footer {{
            text-align: center;
            color: #475569;
            font-size: 0.8rem;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #1e293b;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        .stat-card {{
            background: #1e293b;
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            border: 1px solid #334155;
        }}
        .stat-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #f8fafc;
        }}
        .stat-label {{
            color: #64748b;
            font-size: 0.8rem;
            margin-top: 0.25rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>GuardPilot Compliance Report</h1>
            <p class="subtitle">AI Agent Behavior Compliance Check</p>
        </div>

        <div class="score-card">
            <div class="score-value">{result.score:.0f}</div>
            <div class="score-label">Compliance Score</div>
            <div class="score-bar-container">
                <div class="score-bar" style="width: {result.score}%"></div>
            </div>
            <div class="status-badge-large">{status_text}</div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(result.violations)}</div>
                <div class="stat-label">Violations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(result.warnings)}</div>
                <div class="stat-label">Warnings</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(result.message)}</div>
                <div class="stat-label">Message Length</div>
            </div>
        </div>

        <div class="section">
            <h2>Violations</h2>
            {violations_html if violations_html else '<p class="no-issues">No violations found.</p>'}
        </div>

        <div class="section">
            <h2>Warnings</h2>
            {warnings_html if warnings_html else '<p class="no-issues">No warnings found.</p>'}
        </div>

        <div class="section">
            <h2>Detailed Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rule</th>
                        <th>Status</th>
                        <th>Severity</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {results_rows}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Message Preview</h2>
            <div class="message-preview">{preview}</div>
        </div>

        <div class="footer">
            <p>Generated by GuardPilot v1.0.0 | {self.timestamp}</p>
        </div>
    </div>
</body>
</html>"""

    def generate_html_conversation(
        self, results: list[ComplianceResult]
    ) -> str:
        """Generate an HTML report for a full conversation check.

        Args:
            results: List of compliance results for each message.

        Returns:
            Complete HTML document string.
        """
        total_score = sum(r.score for r in results) / len(results) if results else 100.0
        all_passed = all(r.passed for r in results)

        score_color = (
            "#4ade80" if total_score >= 80
            else "#facc15" if total_score >= 60
            else "#f87171"
        )
        status_text = "ALL PASSED" if all_passed else "ISSUES FOUND"
        status_color = "#4ade80" if all_passed else "#f87171"

        messages_html = ""
        for i, result in enumerate(results, 1):
            msg_score_color = (
                "#4ade80" if result.score >= 80
                else "#facc15" if result.score >= 60
                else "#f87171"
            )
            msg_status = "PASS" if result.passed else "FAIL"
            msg_status_color = "#4ade80" if result.passed else "#f87171"

            issues_html = ""
            for v in result.violations:
                issues_html += f'<div class="issue-item"><span class="severity-badge severity-block">BLOCK</span> {self._escape_html(v.rule.name)}: {self._escape_html(v.details)}</div>'
            for w in result.warnings:
                issues_html += f'<div class="issue-item"><span class="severity-badge severity-warn">WARN</span> {self._escape_html(w.rule.name)}: {self._escape_html(w.details)}</div>'
            if not issues_html:
                issues_html = '<p class="no-issues">No issues found.</p>'

            preview = self._escape_html(result.message[:200])
            if len(result.message) > 200:
                preview += "..."

            messages_html += f"""
            <div class="section">
                <div class="message-header">
                    <span class="message-number">Message {i}</span>
                    <span class="message-score" style="color: {msg_score_color}">{result.score:.0f}/100</span>
                    <span class="status-badge-small" style="background: {msg_status_color}20; color: {msg_status_color}; border: 1px solid {msg_status_color}40;">{msg_status}</span>
                </div>
                <div class="message-preview">{preview}</div>
                <div class="issues-container">{issues_html}</div>
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GuardPilot Conversation Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            line-height: 1.6;
            min-height: 100vh;
        }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 2rem; }}
        .header {{ text-align: center; margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid #1e293b; }}
        .header h1 {{ font-size: 1.8rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.5rem; }}
        .header .subtitle {{ color: #94a3b8; font-size: 0.9rem; }}
        .score-card {{ background: #1e293b; border-radius: 12px; padding: 2rem; text-align: center; margin-bottom: 2rem; border: 1px solid #334155; }}
        .score-value {{ font-size: 4rem; font-weight: 800; color: {score_color}; line-height: 1; }}
        .score-label {{ color: #94a3b8; font-size: 0.9rem; margin-top: 0.5rem; }}
        .status-badge-large {{ display: inline-block; padding: 0.4rem 1.2rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; margin-top: 1rem; background: {status_color}20; color: {status_color}; border: 1px solid {status_color}40; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem; }}
        .stat-card {{ background: #1e293b; border-radius: 8px; padding: 1rem; text-align: center; border: 1px solid #334155; }}
        .stat-value {{ font-size: 1.5rem; font-weight: 700; color: #f8fafc; }}
        .stat-label {{ color: #64748b; font-size: 0.8rem; margin-top: 0.25rem; }}
        .section {{ background: #1e293b; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid #334155; }}
        .message-header {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }}
        .message-number {{ font-weight: 600; color: #f8fafc; }}
        .message-score {{ font-weight: 700; font-size: 1.1rem; }}
        .status-badge-small {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }}
        .message-preview {{ background: #0f172a; border-radius: 8px; padding: 0.75rem; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 0.75rem; white-space: pre-wrap; word-break: break-word; }}
        .issues-container {{ margin-top: 0.5rem; }}
        .issue-item {{ padding: 0.4rem 0.6rem; font-size: 0.85rem; color: #cbd5e1; border-radius: 4px; background: #0f172a; margin-bottom: 0.25rem; display: flex; align-items: center; gap: 0.5rem; }}
        .severity-badge {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.05em; white-space: nowrap; }}
        .severity-block {{ background: #f8717120; color: #f87171; border: 1px solid #f8717140; }}
        .severity-warn {{ background: #facc1520; color: #facc15; border: 1px solid #facc1540; }}
        .no-issues {{ color: #64748b; font-style: italic; text-align: center; padding: 0.5rem; }}
        .footer {{ text-align: center; color: #475569; font-size: 0.8rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #1e293b; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>GuardPilot Conversation Report</h1>
            <p class="subtitle">AI Agent Behavior Compliance Check - Full Conversation</p>
        </div>
        <div class="score-card">
            <div class="score-value">{total_score:.0f}</div>
            <div class="score-label">Average Compliance Score</div>
            <div class="status-badge-large">{status_text}</div>
        </div>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(results)}</div>
                <div class="stat-label">Messages</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(1 for r in results if r.passed)}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(len(r.violations) for r in results)}</div>
                <div class="stat-label">Violations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(len(r.warnings) for r in results)}</div>
                <div class="stat-label">Warnings</div>
            </div>
        </div>
        {messages_html}
        <div class="footer">
            <p>Generated by GuardPilot v1.0.0 | {self.timestamp}</p>
        </div>
    </div>
</body>
</html>"""

    def generate_summary(self, result: ComplianceResult) -> str:
        """Generate a colored terminal summary of the compliance result.

        Args:
            result: The compliance result to summarize.

        Returns:
            Colored terminal output string.
        """
        lines: list[str] = []

        # Header
        lines.append("")
        lines.append(bold_text(colored_text("  GuardPilot Compliance Check", Colors.CYAN)))
        lines.append(f"  {'=' * 40}")

        # Score
        score_color = (
            Colors.BRIGHT_GREEN if result.score >= 80
            else Colors.BRIGHT_YELLOW if result.score >= 60
            else Colors.BRIGHT_RED
        )
        lines.append(f"")
        lines.append(f"  Score: {colored_text(f'{result.score:.0f}/100', score_color)}")

        # Status
        if result.passed:
            lines.append(f"  Status: {colored_text('PASSED', Colors.BRIGHT_GREEN)}")
        else:
            lines.append(f"  Status: {colored_text('FAILED', Colors.BRIGHT_RED)}")

        lines.append(f"  Message length: {len(result.message)} characters")
        lines.append(f"")

        # Violations
        if result.violations:
            lines.append(f"  {bold_text(colored_text('Violations:', Colors.RED))}")
            for v in result.violations:
                lines.append(
                    f"    {colored_text('[BLOCK]', Colors.RED)} {v.rule.name} "
                    f"({v.rule.id})"
                )
                lines.append(f"           {v.details}")
            lines.append(f"")

        # Warnings
        if result.warnings:
            lines.append(f"  {bold_text(colored_text('Warnings:', Colors.YELLOW))}")
            for w in result.warnings:
                lines.append(
                    f"    {colored_text('[WARN]', Colors.YELLOW)} {w.rule.name} "
                    f"({w.rule.id})"
                )
                lines.append(f"           {w.details}")
            lines.append(f"")

        if not result.violations and not result.warnings:
            lines.append(f"  {colored_text('All checks passed. No issues found.', Colors.BRIGHT_GREEN)}")
            lines.append(f"")

        lines.append(f"  {'=' * 40}")
        lines.append(f"  {colored_text('Generated by GuardPilot v1.0.0', Colors.GRAY)}")
        lines.append(f"")

        return "\n".join(lines)

    def generate_summary_conversation(
        self, results: list[ComplianceResult]
    ) -> str:
        """Generate a colored terminal summary for a conversation check.

        Args:
            results: List of compliance results for each message.

        Returns:
            Colored terminal output string.
        """
        total_score = sum(r.score for r in results) / len(results) if results else 100.0
        all_passed = all(r.passed for r in results)

        lines: list[str] = []
        lines.append("")
        lines.append(bold_text(colored_text("  GuardPilot Conversation Check", Colors.CYAN)))
        lines.append(f"  {'=' * 45}")

        score_color = (
            Colors.BRIGHT_GREEN if total_score >= 80
            else Colors.BRIGHT_YELLOW if total_score >= 60
            else Colors.BRIGHT_RED
        )
        lines.append(f"")
        lines.append(f"  Messages checked: {len(results)}")
        lines.append(f"  Average score: {colored_text(f'{total_score:.1f}/100', score_color)}")

        if all_passed:
            lines.append(f"  Overall: {colored_text('ALL PASSED', Colors.BRIGHT_GREEN)}")
        else:
            lines.append(f"  Overall: {colored_text('ISSUES FOUND', Colors.BRIGHT_RED)}")

        total_v = sum(len(r.violations) for r in results)
        total_w = sum(len(r.warnings) for r in results)
        lines.append(f"  Total violations: {colored_text(str(total_v), Colors.RED if total_v > 0 else Colors.GREEN)}")
        lines.append(f"  Total warnings: {colored_text(str(total_w), Colors.YELLOW if total_w > 0 else Colors.GREEN)}")
        lines.append(f"")

        for i, result in enumerate(results, 1):
            msg_color = (
                Colors.BRIGHT_GREEN if result.score >= 80
                else Colors.BRIGHT_YELLOW if result.score >= 60
                else Colors.BRIGHT_RED
            )
            status = colored_text("PASS", Colors.BRIGHT_GREEN) if result.passed else colored_text("FAIL", Colors.BRIGHT_RED)
            lines.append(
                f"  Message {i}: {colored_text(f'{result.score:.0f}', msg_color)}/100 "
                f"[{status}]"
            )
            if result.violations:
                for v in result.violations:
                    lines.append(f"    {colored_text('[BLOCK]', Colors.RED)} {v.rule.name}")
            if result.warnings:
                for w in result.warnings:
                    lines.append(f"    {colored_text('[WARN]', Colors.YELLOW)} {w.rule.name}")

        lines.append(f"")
        lines.append(f"  {'=' * 45}")
        lines.append(f"  {colored_text('Generated by GuardPilot v1.0.0', Colors.GRAY)}")
        lines.append(f"")

        return "\n".join(lines)

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters in a string.

        Args:
            text: The text to escape.

        Returns:
            HTML-safe string.
        """
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )
