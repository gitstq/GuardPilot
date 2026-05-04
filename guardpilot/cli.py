"""CLI entry point for GuardPilot.

Provides the main command-line interface with subcommands for
initializing rules files, validating rules, checking messages
and conversations, generating reports, and listing rules.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .engine import RuleEngine
from .reporter import Reporter
from .templates import get_example_conversation, get_example_rules
from .utils import Colors, bold_text, colored_text, load_file


def _print_banner() -> None:
    """Print the GuardPilot banner."""
    banner = r"""
   ____                 __  __
  / __ \__  _________  / /_/ /_  ____  ____  _____
 / / / / / / / ___/ / / __/ __ \/ __ \/ __ \/ ___/
/ /_/ / /_/ / /  / /_/ /_/ / / / /_/ / /_/ (__  )
\___\_\__,_/_/  \__, /\__/_/ /_/\____/\____/____/
                /____/
"""
    print(colored_text(banner, Colors.CYAN))
    print(colored_text(f"  AI Agent Behavior Compliance Rule Engine v{__version__}", Colors.BRIGHT_CYAN))
    print(colored_text("  " + "=" * 50, Colors.GRAY))
    print()


def cmd_init(args: argparse.Namespace) -> int:
    """Handle the 'init' command - create example rules file.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    rules_path = Path(args.output) if args.output else Path("guardpilot_rules.yaml")
    conv_path = Path("example_conversation.json")

    try:
        rules_content = get_example_rules()
        rules_path.write_text(rules_content, encoding="utf-8")
        print(colored_text(f"[OK]", Colors.BRIGHT_GREEN) + f" Created rules file: {rules_path}")

        conv_content = get_example_conversation()
        conv_path.write_text(conv_content, encoding="utf-8")
        print(colored_text(f"[OK]", Colors.BRIGHT_GREEN) + f" Created example conversation: {conv_path}")

        print()
        print(colored_text("Next steps:", Colors.BRIGHT_CYAN))
        print(f"  1. Edit {rules_path} to customize your compliance rules")
        print(f"  2. Run: guardpilot validate {rules_path}")
        print(f"  3. Run: guardpilot check --rules {rules_path} --conversation {conv_path}")
        return 0
    except Exception as exc:
        print(colored_text(f"[ERROR]", Colors.RED) + f" Failed to create files: {exc}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Handle the 'validate' command - validate a rules file.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    rules_path = Path(args.file)

    if not rules_path.exists():
        print(colored_text(f"[ERROR]", Colors.RED) + f" File not found: {rules_path}")
        return 1

    try:
        engine = RuleEngine()
        rules = engine.load_rules(rules_path)

        print(colored_text(f"[OK]", Colors.BRIGHT_GREEN) + f" Rules file is valid: {rules_path}")
        print(f"  Loaded {len(rules)} rules")

        # Show rule summary
        categories: dict[str, int] = {}
        priorities: dict[str, int] = {}
        for rule in rules:
            categories[rule.category] = categories.get(rule.category, 0) + 1
            priorities[rule.priority] = priorities.get(rule.priority, 0) + 1

        print()
        print(colored_text("  Categories:", Colors.BRIGHT_CYAN))
        for cat, count in sorted(categories.items()):
            print(f"    - {cat}: {count} rules")

        print()
        print(colored_text("  Priorities:", Colors.BRIGHT_CYAN))
        for pri in ["high", "medium", "low"]:
            count = priorities.get(pri, 0)
            if count > 0:
                color = Colors.RED if pri == "high" else Colors.YELLOW if pri == "medium" else Colors.GREEN
                print(f"    - {pri}: {colored_text(str(count), color)}")

        # Check for conflicts
        conflicts = engine.detect_conflicts()
        if conflicts:
            print()
            print(colored_text(f"  [!] Found {len(conflicts)} potential rule conflicts:", Colors.YELLOW))
            for conflict in conflicts:
                print(f"    - {conflict['reason']}")

        return 0
    except Exception as exc:
        print(colored_text(f"[ERROR]", Colors.RED) + f" Validation failed: {exc}")
        return 1


def cmd_check(args: argparse.Namespace) -> int:
    """Handle the 'check' command - check a message or conversation.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error or violations).
    """
    if not args.rules:
        print(colored_text(f"[ERROR]", Colors.RED) + " --rules is required for check command")
        return 1

    rules_path = Path(args.rules)
    if not rules_path.exists():
        print(colored_text(f"[ERROR]", Colors.RED) + f" Rules file not found: {rules_path}")
        return 1

    try:
        engine = RuleEngine()
        engine.load_rules(rules_path)
        reporter = Reporter()

        if args.message:
            # Single message check
            result = engine.check_message(args.message)
            print(reporter.generate_summary(result))
            return 0 if result.passed else 2

        elif args.conversation:
            # Conversation check
            conv_path = Path(args.conversation)
            if not conv_path.exists():
                print(colored_text(f"[ERROR]", Colors.RED) + f" Conversation file not found: {conv_path}")
                return 1

            results = engine.check_conversation(str(conv_path))
            print(reporter.generate_summary_conversation(results))

            all_passed = all(r.passed for r in results)
            return 0 if all_passed else 2

        else:
            print(colored_text(f"[ERROR]", Colors.RED) + " Either --message or --conversation is required")
            return 1

    except Exception as exc:
        print(colored_text(f"[ERROR]", Colors.RED) + f" Check failed: {exc}")
        return 1


def cmd_report(args: argparse.Namespace) -> int:
    """Handle the 'report' command - generate a compliance report.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    if not args.rules:
        print(colored_text(f"[ERROR]", Colors.RED) + " --rules is required for report command")
        return 1

    if not args.conversation:
        print(colored_text(f"[ERROR]", Colors.RED) + " --conversation is required for report command")
        return 1

    rules_path = Path(args.rules)
    conv_path = Path(args.conversation)

    if not rules_path.exists():
        print(colored_text(f"[ERROR]", Colors.RED) + f" Rules file not found: {rules_path}")
        return 1

    if not conv_path.exists():
        print(colored_text(f"[ERROR]", Colors.RED) + f" Conversation file not found: {conv_path}")
        return 1

    fmt = args.format or "markdown"

    try:
        engine = RuleEngine()
        engine.load_rules(rules_path)
        reporter = Reporter()

        results = engine.check_conversation(str(conv_path))

        if len(results) == 1:
            result = results[0]
            if fmt == "json":
                output = reporter.generate_json(result)
            elif fmt == "html":
                output = reporter.generate_html(result)
            else:
                output = reporter.generate_markdown(result)
        else:
            if fmt == "json":
                output = reporter.generate_json_conversation(results)
            elif fmt == "html":
                output = reporter.generate_html_conversation(results)
            else:
                output = reporter.generate_markdown_conversation(results)

        # Write to file or stdout
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(output, encoding="utf-8")
            print(colored_text(f"[OK]", Colors.BRIGHT_GREEN) + f" Report saved to: {output_path}")
        else:
            print(output)

        return 0
    except Exception as exc:
        print(colored_text(f"[ERROR]", Colors.RED) + f" Report generation failed: {exc}")
        return 1


def cmd_rules(args: argparse.Namespace) -> int:
    """Handle the 'rules' subcommands - list or manage rules.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    if args.rules_action == "list":
        if not args.rules:
            print(colored_text(f"[ERROR]", Colors.RED) + " --rules is required for rules list command")
            return 1

        rules_path = Path(args.rules)
        if not rules_path.exists():
            print(colored_text(f"[ERROR]", Colors.RED) + f" Rules file not found: {rules_path}")
            return 1

        try:
            engine = RuleEngine()
            rules = engine.load_rules(rules_path)

            if not rules:
                print(colored_text("  No rules loaded.", Colors.YELLOW))
                return 0

            print()
            print(bold_text(colored_text("  Loaded Rules:", Colors.CYAN)))
            print(f"  {'-' * 60}")

            priority_colors = {
                "high": Colors.RED,
                "medium": Colors.YELLOW,
                "low": Colors.GREEN,
            }
            severity_icons = {
                "block": colored_text("BLOCK", Colors.RED),
                "warn": colored_text("WARN ", Colors.YELLOW),
                "log": colored_text("LOG  ", Colors.GRAY),
            }

            for rule in rules:
                pri_color = priority_colors.get(rule.priority, Colors.WHITE)
                status = colored_text("ON ", Colors.BRIGHT_GREEN) if rule.enabled else colored_text("OFF", Colors.GRAY)
                sev = severity_icons.get(rule.severity, rule.severity)

                print(f"  {status} | {colored_text(rule.priority.upper(), pri_color):>6} | {sev} | {rule.name}")
                if rule.description:
                    print(f"         {rule.description[:70]}{'...' if len(rule.description) > 70 else ''}")
                print(f"         ID: {rule.id} | Category: {rule.category} | Conditions: {len(rule.conditions)}")
                print()

            print(f"  {'-' * 60}")
            print(f"  Total: {len(rules)} rules ({sum(1 for r in rules if r.enabled)} enabled)")
            return 0

        except Exception as exc:
            print(colored_text(f"[ERROR]", Colors.RED) + f" Failed to load rules: {exc}")
            return 1

    print(colored_text(f"[ERROR]", Colors.RED) + f" Unknown rules action: {args.rules_action}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="guardpilot",
        description="GuardPilot - AI Agent Behavior Compliance Rule Engine",
        epilog="Example: guardpilot check --rules rules.yaml --message 'Hello world'",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"GuardPilot v{__version__}",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        default=False,
        help="Suppress the startup banner",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    init_parser = subparsers.add_parser("init", help="Create example rules YAML file")
    init_parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (default: guardpilot_rules.yaml)",
    )

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a rules file syntax")
    validate_parser.add_argument(
        "file",
        type=str,
        help="Path to the rules YAML file",
    )

    # check command
    check_parser = subparsers.add_parser("check", help="Check a message or conversation against rules")
    check_parser.add_argument(
        "--rules",
        type=str,
        required=True,
        help="Path to the rules YAML file",
    )
    check_parser.add_argument(
        "--message",
        type=str,
        default=None,
        help="Agent response message to check",
    )
    check_parser.add_argument(
        "--conversation",
        type=str,
        default=None,
        help="Path to conversation JSON file",
    )

    # report command
    report_parser = subparsers.add_parser("report", help="Generate compliance report")
    report_parser.add_argument(
        "--rules",
        type=str,
        required=True,
        help="Path to the rules YAML file",
    )
    report_parser.add_argument(
        "--conversation",
        type=str,
        required=True,
        help="Path to conversation JSON file",
    )
    report_parser.add_argument(
        "--format",
        type=str,
        choices=["json", "html", "markdown"],
        default="markdown",
        help="Report format (default: markdown)",
    )
    report_parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (default: stdout)",
    )

    # rules command
    rules_parser = subparsers.add_parser("rules", help="Manage and inspect rules")
    rules_subparsers = rules_parser.add_subparsers(dest="rules_action", help="Rules subcommands")

    rules_list_parser = rules_subparsers.add_parser("list", help="List all loaded rules with priorities")
    rules_list_parser.add_argument(
        "--rules",
        type=str,
        required=True,
        help="Path to the rules YAML file",
    )

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for the GuardPilot CLI.

    Args:
        argv: Optional command-line arguments. If None, uses sys.argv.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Show banner unless suppressed
    if not getattr(args, "no_banner", False) and args.command is not None:
        _print_banner()

    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "init": cmd_init,
        "validate": cmd_validate,
        "check": cmd_check,
        "report": cmd_report,
        "rules": cmd_rules,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
