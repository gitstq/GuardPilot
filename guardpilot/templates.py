"""Built-in templates for GuardPilot.

Provides example rules YAML content and example conversation JSON
for quick-start and demonstration purposes.
"""

from __future__ import annotations


def get_example_rules() -> str:
    """Return example rules YAML content as a string.

    Includes content safety rules, response format rules,
    domain-specific rules, and tone/style rules with both
    English and Chinese examples.

    Returns:
        YAML-formatted string with example compliance rules.
    """
    return '''# GuardPilot Compliance Rules Example
# This file defines behavioral rules for AI agent responses.
# Rules are evaluated in priority order (high > medium > low).

rules:
  # ========================================
  # Content Safety Rules / 内容安全规则
  # ========================================
  - id: no-harmful-content
    name: No Harmful Content / 禁止有害内容
    description: Agent responses must not contain harmful, violent, or illegal content. Agent responses must not contain harmful, violent, or illegal content.
    category: content_safety
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value: harmful
        negate: true
      - type: keyword
        value: violence
        negate: true
      - type: keyword
        value: illegal
        negate: true

  - id: no-pii-leakage
    name: No PII Leakage / 禁止泄露个人信息
    description: Agent must not expose personally identifiable information such as SSN, credit card numbers, or ID numbers.
    category: content_safety
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: regex
        value: "\\b\\d{3}-\\d{2}-\\d{4}\\b"
        negate: true
      - type: regex
        value: "\\b\\d{16,19}\\b"
        negate: true
      - type: keyword
        value: 身份证号
        negate: true

  - id: no-profanity
    name: No Profanity / 禁止粗俗语言
    description: Agent responses must not contain profane or offensive language.
    category: content_safety
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value: damn
        negate: true
      - type: keyword
        value: shit
        negate: true

  # ========================================
  # Response Format Rules / 响应格式规则
  # ========================================
  - id: max-response-length
    name: Max Response Length / 最大响应长度
    description: Agent responses should not exceed 2000 characters to maintain readability.
    category: response_format
    priority: medium
    severity: warn
    enabled: true
    conditions:
      - type: length
        value: 2000
        negate: true

  - id: require-greeting
    name: Require Greeting / 需要问候语
    description: Agent should start responses with a polite greeting in customer service scenarios.
    category: response_format
    priority: low
    severity: log
    enabled: true
    conditions:
      - type: keyword
        value: Hello
      - type: keyword
        value: 您好

  # ========================================
  # Domain Compliance Rules / 领域合规规则
  # ========================================
  - id: financial-disclaimer
    name: Financial Disclaimer / 金融免责声明
    description: Financial advice responses must include a disclaimer. Financial advice responses must include a disclaimer.
    category: domain_compliance
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value: disclaimer
      - type: keyword
        value: 免责声明

  - id: medical-disclaimer
    name: Medical Disclaimer / 医疗免责声明
    description: Medical advice responses must include a consultation recommendation.
    category: domain_compliance
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value: consult
      - type: keyword
        value: 就医

  - id: legal-disclaimer
    name: Legal Disclaimer / 法律免责声明
    description: Legal advice responses must recommend consulting a qualified attorney.
    category: domain_compliance
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value: attorney
      - type: keyword
        value: 律师

  # ========================================
  # Tone and Style Rules / 语气风格规则
  # ========================================
  - id: professional-language
    name: Professional Language / 专业语言
    description: Agent should use professional and formal language.
    category: tone_style
    priority: medium
    severity: warn
    enabled: true
    conditions:
      - type: keyword
        value: lol
        negate: true
      - type: keyword
        value: omg
        negate: true

  - id: no-jargon
    name: No Excessive Jargon / 避免过多术语
    description: Agent should explain technical terms when used, avoiding excessive jargon.
    category: tone_style
    priority: low
    severity: log
    enabled: true
    conditions:
      - type: keyword
        value: API
        negate: true
      - type: keyword
        value: Kubernetes
        negate: true
'''


def get_example_conversation() -> str:
    """Return example conversation JSON content as a string.

    Includes a multi-turn conversation with user, assistant, and
    system messages for testing compliance checks.

    Returns:
        JSON-formatted string with example conversation data.
    """
    return '''{
  "metadata": {
    "conversation_id": "conv-001",
    "agent_name": "FinanceBot",
    "created_at": "2025-01-15T10:30:00Z"
  },
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful financial assistant. Always include appropriate disclaimers when providing financial advice.",
      "timestamp": "2025-01-15T10:30:00Z"
    },
    {
      "role": "user",
      "content": "What stocks should I invest in right now?",
      "timestamp": "2025-01-15T10:30:15Z"
    },
    {
      "role": "assistant",
      "content": "Hello! I can provide some general information about investment strategies. However, please note that this is not financial advice and you should consult a qualified financial advisor before making any investment decisions. Consider diversifying your portfolio across different asset classes and risk levels.",
      "timestamp": "2025-01-15T10:30:30Z"
    },
    {
      "role": "user",
      "content": "Tell me more about diversification strategies.",
      "timestamp": "2025-01-15T10:31:00Z"
    },
    {
      "role": "assistant",
      "content": "Diversification involves spreading your investments across various assets to reduce risk. This can include stocks, bonds, real estate, and commodities. A well-diversified portfolio can help protect against significant losses in any single investment. Remember, past performance does not guarantee future results.",
      "timestamp": "2025-01-15T10:31:20Z"
    }
  ]
}'''
