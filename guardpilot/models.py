"""Data models for GuardPilot rule engine.

Defines the core data structures used throughout the application:
rules, conditions, compliance results, conversations, and messages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Priority(str, Enum):
    """Rule priority levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Severity(str, Enum):
    """Rule violation severity levels."""

    BLOCK = "block"
    WARN = "warn"
    LOG = "log"


class ConditionType(str, Enum):
    """Types of conditions that can be applied to rules."""

    KEYWORD = "keyword"
    REGEX = "regex"
    PATTERN = "pattern"
    LENGTH = "length"
    CUSTOM = "custom"


class MessageRole(str, Enum):
    """Roles in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Condition:
    """A single condition within a rule.

    Attributes:
        type: The type of condition (keyword, regex, pattern, length, custom).
        value: The value to match against (keyword, regex pattern, etc.).
        negate: If True, the condition is inverted (match when NOT found).
    """

    type: str = "keyword"
    value: Any = ""
    negate: bool = False


@dataclass
class Rule:
    """A compliance rule definition.

    Attributes:
        id: Unique identifier for the rule.
        name: Human-readable rule name.
        description: Detailed description of what the rule checks.
        category: Category grouping (e.g., 'content_safety', 'format').
        priority: Priority level (high, medium, low).
        conditions: List of conditions that must be satisfied.
        severity: Severity when the rule is violated (block, warn, log).
        enabled: Whether the rule is active.
    """

    id: str = ""
    name: str = ""
    description: str = ""
    category: str = "general"
    priority: str = "medium"
    conditions: list[Condition] = field(default_factory=list)
    severity: str = "warn"
    enabled: bool = True


@dataclass
class RuleResult:
    """Result of checking a single rule against a message.

    Attributes:
        rule: The rule that was checked.
        matched: Whether the rule condition was triggered.
        details: Human-readable explanation of the result.
        severity: The severity level of the rule.
    """

    rule: Rule = field(default_factory=Rule)
    matched: bool = False
    details: str = ""
    severity: str = "warn"


@dataclass
class ComplianceResult:
    """Result of checking a message or conversation against all rules.

    Attributes:
        message: The message that was checked.
        rule_results: List of individual rule check results.
        score: Compliance score from 0 to 100.
        passed: Whether the message passed all checks (no block-level violations).
        violations: List of rule results that triggered block-level violations.
        warnings: List of rule results that triggered warn-level violations.
    """

    message: str = ""
    rule_results: list[RuleResult] = field(default_factory=list)
    score: float = 100.0
    passed: bool = True
    violations: list[RuleResult] = field(default_factory=list)
    warnings: list[RuleResult] = field(default_factory=list)


@dataclass
class Message:
    """A single message in a conversation.

    Attributes:
        role: The role of the message sender (user, assistant, system).
        content: The text content of the message.
        timestamp: ISO format timestamp of when the message was sent.
    """

    role: str = "assistant"
    content: str = ""
    timestamp: Optional[str] = None


@dataclass
class Conversation:
    """A conversation consisting of multiple messages.

    Attributes:
        messages: Ordered list of messages in the conversation.
        metadata: Optional metadata about the conversation.
    """

    messages: list[Message] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, timestamp: Optional[str] = None) -> None:
        """Add a new message to the conversation.

        Args:
            role: The role of the message sender.
            content: The text content of the message.
            timestamp: Optional ISO format timestamp.
        """
        self.messages.append(Message(role=role, content=content, timestamp=timestamp))

    def get_assistant_messages(self) -> list[Message]:
        """Get all messages sent by the assistant.

        Returns:
            List of assistant messages.
        """
        return [m for m in self.messages if m.role == "assistant"]

    def to_dict(self) -> dict[str, Any]:
        """Convert conversation to a dictionary.

        Returns:
            Dictionary representation of the conversation.
        """
        return {
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                for m in self.messages
            ],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Conversation:
        """Create a Conversation from a dictionary.

        Args:
            data: Dictionary with 'messages' key containing message dicts.

        Returns:
            A Conversation instance.
        """
        messages = []
        for msg_data in data.get("messages", []):
            messages.append(
                Message(
                    role=msg_data.get("role", "assistant"),
                    content=msg_data.get("content", ""),
                    timestamp=msg_data.get("timestamp"),
                )
            )
        return cls(messages=messages, metadata=data.get("metadata", {}))
