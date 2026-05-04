"""Utility functions for GuardPilot.

Provides YAML parsing, colored terminal output, timestamp formatting,
and text similarity calculations. All implemented with zero external
dependencies using only Python stdlib.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union


# ---------------------------------------------------------------------------
# ANSI Color Codes
# ---------------------------------------------------------------------------

class Colors:
    """ANSI color code constants for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"

    # Bright foreground
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


def colored_text(text: str, color: str) -> str:
    """Wrap text with ANSI color codes.

    Args:
        text: The text to colorize.
        color: ANSI color code string (e.g., Colors.RED, Colors.GREEN).

    Returns:
        Colorized text string with reset code appended.
    """
    return f"{color}{text}{Colors.RESET}"


def bold_text(text: str) -> str:
    """Make text bold in terminal output.

    Args:
        text: The text to make bold.

    Returns:
        Bold text string.
    """
    return f"{Colors.BOLD}{text}{Colors.RESET}"


def format_timestamp() -> str:
    """Get current timestamp in ISO 8601 format.

    Returns:
        ISO format timestamp string with timezone info.
    """
    return datetime.now(timezone.utc).isoformat()


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard word similarity between two texts.

    Tokenizes both texts into lowercase words and computes the
    Jaccard similarity coefficient (intersection / union).

    Args:
        text1: First text string.
        text2: Second text string.

    Returns:
        Similarity score between 0.0 (no overlap) and 1.0 (identical).
    """
    if not text1 or not text2:
        return 0.0

    words1 = set(re.findall(r"\w+", text1.lower()))
    words2 = set(re.findall(r"\w+", text2.lower()))

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)


# ---------------------------------------------------------------------------
# Minimal YAML Subset Parser
# ---------------------------------------------------------------------------

class YAMLParseError(Exception):
    """Raised when YAML parsing fails."""

    pass


def _strip_comment(line: str) -> str:
    """Remove inline comments from a YAML line.

    Handles the case where '#' appears inside quoted strings.

    Args:
        line: A single line of YAML text.

    Returns:
        The line with comments removed.
    """
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '#' and not in_single and not in_double:
            # Check if '#' is preceded by whitespace or is at start
            if i == 0 or line[i - 1] in (' ', '\t'):
                return line[:i].rstrip()
    return line.rstrip()


def _parse_scalar(value: str) -> Union[str, int, float, bool, None]:
    """Parse a YAML scalar value into the appropriate Python type.

    Handles booleans, null, integers, floats, and strings.

    Args:
        value: The string representation of the scalar.

    Returns:
        Parsed Python value.
    """
    stripped = value.strip()

    # Remove surrounding quotes
    if len(stripped) >= 2:
        if (stripped[0] == '"' and stripped[-1] == '"') or \
           (stripped[0] == "'" and stripped[-1] == "'"):
            return stripped[1:-1]

    # Booleans
    if stripped.lower() in ('true', 'yes', 'on'):
        return True
    if stripped.lower() in ('false', 'no', 'off'):
        return False

    # Null
    if stripped.lower() in ('null', '~', ''):
        return None

    # Integer
    try:
        return int(stripped)
    except ValueError:
        pass

    # Float
    try:
        return float(stripped)
    except ValueError:
        pass

    return stripped


def _get_indent(line: str) -> int:
    """Calculate the indentation level of a line.

    Args:
        line: A line of YAML text.

    Returns:
        Number of leading spaces.
    """
    return len(line) - len(line.lstrip(' '))


def _parse_yaml_lines(lines: list[str]) -> Any:
    """Parse preprocessed YAML lines into a Python data structure.

    Recursively handles mappings, sequences, and nested structures.

    Args:
        lines: List of YAML lines (comments already stripped).

    Returns:
        Parsed Python object (dict, list, or scalar).
    """
    if not lines:
        return None

    # Filter out empty lines
    non_empty = [(i, line) for i, line in enumerate(lines) if line.strip()]
    if not non_empty:
        return None

    first_idx, first_line = non_empty[0]
    stripped = first_line.strip()

    # Check if this is a sequence (starts with '- ')
    if stripped.startswith('- ') or stripped == '-':
        return _parse_sequence(lines, first_idx)

    # Check if this is a mapping (contains ':')
    if ':' in stripped and not stripped.startswith('-'):
        return _parse_mapping(lines, first_idx)

    # Scalar value
    return _parse_scalar(stripped)


def _parse_sequence(lines: list[str], start_idx: int) -> list[Any]:
    """Parse a YAML sequence starting at the given line index.

    Args:
        lines: All YAML lines.
        start_idx: Index of the first sequence item.

    Returns:
        List of parsed values.
    """
    result: list[Any] = []
    base_indent = _get_indent(lines[start_idx])

    i = start_idx
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        indent = _get_indent(line)
        stripped = line.strip()

        if indent < base_indent:
            break

        if indent == base_indent and (stripped.startswith('- ') or stripped == '-'):
            # Sequence item
            item_value = stripped[2:].strip() if len(stripped) > 2 else ""

            if not item_value:
                # Value is on next lines with greater indentation
                sub_lines = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if not next_line.strip():
                        j += 1
                        continue
                    next_indent = _get_indent(next_line)
                    if next_indent <= base_indent:
                        break
                    sub_lines.append(next_line)
                    j += 1
                if sub_lines:
                    parsed = _parse_yaml_lines(sub_lines)
                    result.append(parsed if parsed is not None else None)
                else:
                    result.append(None)
                i = j
            elif ':' in item_value:
                # Inline mapping: "- key: value" or "- key:"
                # Collect all sub-lines that belong to this item
                sub_lines = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if not next_line.strip():
                        j += 1
                        continue
                    next_indent = _get_indent(next_line)
                    if next_indent <= base_indent:
                        break
                    sub_lines.append(next_line)
                    j += 1

                # Reconstruct as a mapping by stripping the "- " prefix
                # and treating the rest as a mapping entry.
                # The "- " takes 2 chars, so the content starts at base_indent + 2
                content_indent = base_indent + 2
                mapping_line = ' ' * content_indent + item_value
                full_lines = [mapping_line] + sub_lines
                parsed = _parse_yaml_lines(full_lines)
                if isinstance(parsed, dict):
                    result.append(parsed)
                else:
                    # Fallback: parse as scalar
                    result.append(_parse_scalar(item_value))
                i = j
            else:
                # Inline scalar value
                result.append(_parse_scalar(item_value))
                i += 1
        elif indent > base_indent:
            # Continuation of previous item (nested structure)
            i += 1
        else:
            break

    return result


def _parse_mapping(lines: list[str], start_idx: int) -> dict[str, Any]:
    """Parse a YAML mapping starting at the given line index.

    Args:
        lines: All YAML lines.
        start_idx: Index of the first mapping entry.

    Returns:
        Dictionary of parsed key-value pairs.
    """
    result: dict[str, Any] = {}
    base_indent = _get_indent(lines[start_idx])

    i = start_idx
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        indent = _get_indent(line)
        stripped = line.strip()

        if indent < base_indent:
            break

        if indent > base_indent:
            i += 1
            continue

        # Must be a key: value line
        if ':' not in stripped:
            i += 1
            continue

        colon_pos = stripped.index(':')
        key = stripped[:colon_pos].strip()
        value_part = stripped[colon_pos + 1:].strip()

        if not value_part:
            # Value is on subsequent lines
            sub_lines = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if not next_line.strip():
                    j += 1
                    continue
                next_indent = _get_indent(next_line)
                if next_indent <= base_indent:
                    break
                sub_lines.append(next_line)
                j += 1

            if sub_lines:
                parsed = _parse_yaml_lines(sub_lines)
                result[key] = parsed if parsed is not None else None
            else:
                result[key] = None
            i = j
        elif value_part.startswith('|') or value_part.startswith('>'):
            # Block scalar (literal or folded)
            block_type = value_part[0]
            chomp = value_part[1:].strip() if len(value_part) > 1 else ""

            # Determine the block indent from the next non-empty line
            j = i + 1
            block_indent = None
            block_lines: list[str] = []
            while j < len(lines):
                next_line = lines[j]
                if not next_line.strip():
                    block_lines.append("")
                    j += 1
                    continue
                next_indent = _get_indent(next_line)
                if block_indent is None:
                    block_indent = next_indent
                if next_indent < block_indent:
                    break
                block_lines.append(next_line[block_indent:])
                j += 1

            # Join block lines
            if block_type == '|':
                # Literal: preserve newlines
                text = '\n'.join(block_lines)
            else:
                # Folded: replace single newlines with spaces
                text = ''
                for k, bl in enumerate(block_lines):
                    if bl == '':
                        text += '\n'
                    elif k == 0:
                        text = bl
                    else:
                        text += ' ' + bl

            # Handle chomping
            if chomp == '-':
                text = text.rstrip('\n')
            elif chomp == '+':
                text = text + '\n'
            else:
                text = text.rstrip('\n') + '\n'

            result[key] = text
            i = j
        else:
            # Inline value
            result[key] = _parse_scalar(value_part)
            i += 1

    return result


def parse_yaml(text: str) -> Any:
    """Parse a YAML string into a Python data structure.

    Supports a subset of YAML: mappings, sequences, scalars
    (strings, numbers, booleans, null), block scalars, and comments.

    Args:
        text: YAML-formatted string.

    Returns:
        Parsed Python object (dict, list, or scalar).

    Raises:
        YAMLParseError: If parsing fails.
    """
    if not text or not text.strip():
        return {}

    lines = text.split('\n')
    processed = []
    for line in lines:
        stripped = _strip_comment(line)
        processed.append(stripped)

    try:
        result = _parse_yaml_lines(processed)
        return result if result is not None else {}
    except Exception as exc:
        raise YAMLParseError(f"Failed to parse YAML: {exc}") from exc


def load_yaml(path: Union[str, Path]) -> Any:
    """Load and parse a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed Python object.

    Raises:
        FileNotFoundError: If the file does not exist.
        YAMLParseError: If parsing fails.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    text = path.read_text(encoding='utf-8')
    return parse_yaml(text)


def load_json(path: Union[str, Path]) -> Any:
    """Load and parse a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed Python object.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If parsing fails.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    text = path.read_text(encoding='utf-8')
    return json.loads(text)


def load_file(path: Union[str, Path]) -> Any:
    """Load a YAML or JSON file based on its extension.

    Args:
        path: Path to the file.

    Returns:
        Parsed Python object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is not supported.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in ('.yaml', '.yml'):
        return load_yaml(path)
    elif suffix == '.json':
        return load_json(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .yaml, .yml, or .json")
