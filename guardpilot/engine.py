"""Core rule engine for GuardPilot.

Provides the RuleEngine class that loads rules from YAML files,
checks messages and conversations against those rules, detects
conflicts, and calculates compliance scores.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional, Union

from .models import (
    ComplianceResult,
    Condition,
    Conversation,
    Message,
    Rule,
    RuleResult,
)
from .utils import Colors, calculate_similarity, colored_text, load_file


class RuleEngine:
    """Core compliance rule engine.

    Loads rules from YAML/JSON files and evaluates messages
    and conversations against those rules to produce compliance
    results with scores and violation details.
    """

    def __init__(self) -> None:
        """Initialize the rule engine with empty rules list."""
        self.rules: list[Rule] = []

    def load_rules(self, yaml_path: Union[str, Path]) -> list[Rule]:
        """Load rules from a YAML or JSON file.

        Args:
            yaml_path: Path to the rules file.

        Returns:
            List of loaded Rule objects.

        Raises:
            FileNotFoundError: If the rules file does not exist.
            ValueError: If the rules file format is invalid.
        """
        data = load_file(yaml_path)

        if not isinstance(data, dict):
            raise ValueError("Rules file must contain a mapping at the top level")

        raw_rules = data.get("rules", [])
        if not isinstance(raw_rules, list):
            raise ValueError("'rules' key must contain a list of rule definitions")

        self.rules = []
        for raw_rule in raw_rules:
            rule = self._parse_rule(raw_rule)
            if rule is not None:
                self.rules.append(rule)

        # Sort by priority (high first)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        self.rules.sort(key=lambda r: priority_order.get(r.priority, 3))

        return self.rules

    def _parse_rule(self, raw: dict[str, Any]) -> Optional[Rule]:
        """Parse a raw rule dictionary into a Rule object.

        Args:
            raw: Dictionary containing rule definition.

        Returns:
            A Rule object, or None if the rule is invalid.
        """
        if not isinstance(raw, dict):
            return None

        rule_id = raw.get("id", "")
        if not rule_id:
            return None

        conditions = []
        for raw_cond in raw.get("conditions", []):
            if isinstance(raw_cond, dict):
                conditions.append(
                    Condition(
                        type=raw_cond.get("type", "keyword"),
                        value=raw_cond.get("value", ""),
                        negate=raw_cond.get("negate", False),
                    )
                )

        return Rule(
            id=str(rule_id),
            name=raw.get("name", rule_id),
            description=raw.get("description", ""),
            category=raw.get("category", "general"),
            priority=raw.get("priority", "medium"),
            conditions=conditions,
            severity=raw.get("severity", "warn"),
            enabled=raw.get("enabled", True),
        )

    def check_message(self, message: str, rules: Optional[list[Rule]] = None) -> ComplianceResult:
        """Check a single message against rules.

        Args:
            message: The agent response message to check.
            rules: Optional list of rules. If None, uses loaded rules.

        Returns:
            ComplianceResult with detailed check results and score.
        """
        active_rules = rules if rules is not None else self.rules
        active_rules = [r for r in active_rules if r.enabled]

        rule_results: list[RuleResult] = []
        for rule in active_rules:
            result = self._match_rule(message, rule)
            rule_results.append(result)

        return self._calculate_compliance_score(message, rule_results)

    def check_conversation(
        self,
        conversation: Union[Conversation, dict[str, Any], str],
        rules: Optional[list[Rule]] = None,
    ) -> list[ComplianceResult]:
        """Check a full conversation against rules.

        Only assistant messages are checked against the rules.

        Args:
            conversation: A Conversation object, a dict, or a file path string.
            rules: Optional list of rules. If None, uses loaded rules.

        Returns:
            List of ComplianceResult objects, one per assistant message.
        """
        conv = self._resolve_conversation(conversation)
        active_rules = rules if rules is not None else self.rules

        results: list[ComplianceResult] = []
        for msg in conv.get_assistant_messages():
            result = self.check_message(msg.content, active_rules)
            results.append(result)

        return results

    def _resolve_conversation(
        self, conversation: Union[Conversation, dict[str, Any], str]
    ) -> Conversation:
        """Resolve conversation input to a Conversation object.

        Args:
            conversation: A Conversation object, dict, or file path.

        Returns:
            A Conversation instance.

        Raises:
            FileNotFoundError: If a file path is provided but doesn't exist.
            ValueError: If the input format is not recognized.
        """
        if isinstance(conversation, Conversation):
            return conversation

        if isinstance(conversation, str):
            path = Path(conversation)
            if path.exists():
                data = load_file(path)
                return Conversation.from_dict(data)
            raise FileNotFoundError(f"Conversation file not found: {conversation}")

        if isinstance(conversation, dict):
            return Conversation.from_dict(conversation)

        raise ValueError("Conversation must be a Conversation object, dict, or file path")

    def _match_rule(self, message: str, rule: Rule) -> RuleResult:
        """Check if a message matches a single rule.

        Evaluates all conditions in the rule. A rule is considered
        matched if ANY condition triggers (OR logic for conditions
        with negate=True, AND logic for negate=False).

        Args:
            message: The message text to check.
            rule: The rule to evaluate.

        Returns:
            RuleResult indicating whether the rule was triggered.
        """
        if not rule.conditions:
            return RuleResult(
                rule=rule,
                matched=False,
                details=f"Rule '{rule.name}' has no conditions to evaluate.",
                severity=rule.severity,
            )

        triggered_conditions: list[str] = []
        negated_passes: list[str] = []

        for condition in rule.conditions:
            is_match = self._evaluate_condition(message, condition)

            if condition.negate:
                # Negated condition: if the pattern IS found, it's a violation
                if is_match:
                    triggered_conditions.append(
                        f"Found forbidden pattern ({condition.type}: '{condition.value}')"
                    )
                else:
                    negated_passes.append(
                        f"Negated condition passed ({condition.type}: '{condition.value}')"
                    )
            else:
                # Normal condition: if the pattern is NOT found, it's a violation
                if not is_match:
                    triggered_conditions.append(
                        f"Missing required pattern ({condition.type}: '{condition.value}')"
                    )

        matched = len(triggered_conditions) > 0

        if matched:
            details = f"Rule '{rule.name}' violated: " + "; ".join(triggered_conditions)
        else:
            details = f"Rule '{rule.name}' passed all conditions."

        return RuleResult(
            rule=rule,
            matched=matched,
            details=details,
            severity=rule.severity,
        )

    def _evaluate_condition(self, message: str, condition: Condition) -> bool:
        """Evaluate a single condition against a message.

        Args:
            message: The message text.
            condition: The condition to evaluate.

        Returns:
            True if the condition pattern is found in the message.
        """
        cond_type = condition.type
        value = condition.value

        if cond_type == "keyword":
            return self._match_keyword(message, str(value))

        elif cond_type == "regex":
            return self._match_regex(message, str(value))

        elif cond_type == "pattern":
            return self._match_pattern(message, str(value))

        elif cond_type == "length":
            return self._match_length(message, value)

        elif cond_type == "custom":
            return self._match_custom(message, str(value))

        return False

    def _match_keyword(self, message: str, keyword: str) -> bool:
        """Check if a keyword appears in the message (case-insensitive).

        Args:
            message: The message text.
            keyword: The keyword to search for.

        Returns:
            True if the keyword is found.
        """
        if not keyword:
            return False
        return keyword.lower() in message.lower()

    def _match_regex(self, message: str, pattern: str) -> bool:
        """Check if a regex pattern matches the message.

        Args:
            message: The message text.
            pattern: The regex pattern string.

        Returns:
            True if the pattern matches anywhere in the message.
        """
        if not pattern:
            return False
        try:
            return bool(re.search(pattern, message, re.IGNORECASE))
        except re.error:
            return False

    def _match_pattern(self, message: str, pattern: str) -> bool:
        """Check if a semantic pattern matches using word similarity.

        Uses Jaccard similarity with a threshold of 0.3.

        Args:
            message: The message text.
            pattern: The pattern text to compare against.

        Returns:
            True if similarity exceeds the threshold.
        """
        if not pattern:
            return False
        similarity = calculate_similarity(message, pattern)
        return similarity >= 0.3

    def _match_length(self, message: str, max_length: Any) -> bool:
        """Check if the message exceeds the maximum allowed length.

        Args:
            message: The message text.
            max_length: Maximum allowed length (number).

        Returns:
            True if the message length exceeds the limit (violation).
        """
        try:
            limit = int(max_length)
        except (ValueError, TypeError):
            return False
        return len(message) > limit

    def _match_custom(self, message: str, custom_rule: str) -> bool:
        """Evaluate a custom rule expression.

        Supports simple expressions like 'contains_any:word1,word2'
        or 'starts_with:prefix'.

        Args:
            message: The message text.
            custom_rule: The custom rule expression.

        Returns:
            True if the custom rule matches.
        """
        if ':' not in custom_rule:
            return custom_rule.lower() in message.lower()

        rule_type, rule_value = custom_rule.split(':', 1)
        rule_type = rule_type.strip().lower()
        rule_value = rule_value.strip()

        if rule_type == 'contains_any':
            keywords = [k.strip() for k in rule_value.split(',')]
            return any(kw.lower() in message.lower() for kw in keywords)
        elif rule_type == 'contains_all':
            keywords = [k.strip() for k in rule_value.split(',')]
            return all(kw.lower() in message.lower() for kw in keywords)
        elif rule_type == 'starts_with':
            return message.lower().startswith(rule_value.lower())
        elif rule_type == 'ends_with':
            return message.lower().endswith(rule_value.lower())

        return rule_value.lower() in message.lower()

    def _calculate_compliance_score(
        self, message: str, rule_results: list[RuleResult]
    ) -> ComplianceResult:
        """Calculate compliance score and build the ComplianceResult.

        Score is calculated based on:
        - Each block violation: -20 points
        - Each warn violation: -10 points
        - Each log violation: -5 points
        - Minimum score: 0

        Args:
            message: The checked message.
            rule_results: List of individual rule check results.

        Returns:
            A ComplianceResult with score, violations, and warnings.
        """
        score = 100.0
        violations: list[RuleResult] = []
        warnings: list[RuleResult] = []

        for result in rule_results:
            if result.matched:
                if result.severity == "block":
                    score -= 20
                    violations.append(result)
                elif result.severity == "warn":
                    score -= 10
                    warnings.append(result)
                elif result.severity == "log":
                    score -= 5

        score = max(0.0, min(100.0, score))
        passed = len(violations) == 0

        return ComplianceResult(
            message=message,
            rule_results=rule_results,
            score=score,
            passed=passed,
            violations=violations,
            warnings=warnings,
        )

    def detect_conflicts(self, rules: Optional[list[Rule]] = None) -> list[dict[str, Any]]:
        """Detect potentially conflicting rules.

        Two rules conflict if they have the same category and one
        requires a keyword while another forbids it (negate).

        Args:
            rules: Optional list of rules to check. If None, uses loaded rules.

        Returns:
            List of conflict descriptions as dictionaries.
        """
        active_rules = rules if rules is not None else self.rules
        conflicts: list[dict[str, Any]] = []

        for i, rule_a in enumerate(active_rules):
            for rule_b in active_rules[i + 1:]:
                conflict = self._check_rule_conflict(rule_a, rule_b)
                if conflict:
                    conflicts.append(conflict)

        return conflicts

    def _check_rule_conflict(
        self, rule_a: Rule, rule_b: Rule
    ) -> Optional[dict[str, Any]]:
        """Check if two rules potentially conflict.

        Args:
            rule_a: First rule.
            rule_b: Second rule.

        Returns:
            Conflict description dict, or None if no conflict.
        """
        if rule_a.category != rule_b.category:
            return None

        for cond_a in rule_a.conditions:
            for cond_b in rule_b.conditions:
                if cond_a.type == cond_b.type and cond_a.value == cond_b.value:
                    if cond_a.negate != cond_b.negate:
                        return {
                            "rule_a": rule_a.id,
                            "rule_b": rule_b.id,
                            "category": rule_a.category,
                            "reason": (
                                f"Rule '{rule_a.name}' and '{rule_b.name}' have "
                                f"conflicting conditions on '{cond_a.value}'"
                            ),
                        }

        return None
