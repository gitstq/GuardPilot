<p align="center">
  <a href="README.md">简体中文</a> · <a href="README.zh-TW.md">繁體中文</a> · <a href="README.en.md">English</a>
</p>

<h1 align="center">
  🛡️ GuardPilot
</h1>

<p align="center">
  <strong>Lightweight AI Agent Behavior Compliance Rule Engine</strong><br>
  YAML-driven rules · Zero dependencies · Multi-format compliance reports
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Dependencies-Zero-success.svg" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/Tests-120%20Passed-brightgreen.svg" alt="120 Tests Passed">
  <img src="https://img.shields.io/badge/Version-1.0.0-orange.svg" alt="v1.0.0">
</p>

---

## 🎉 Introduction

**GuardPilot** is a **behavior compliance rule engine** designed specifically for AI/LLM Agents. It helps developers ensure that Agent outputs comply with predefined business rules and behavioral guidelines in production environments.

### 💡 Inspiration

As AI Agents become widely deployed in production, issues like hallucination, instruction non-compliance, and inappropriate content generation have become increasingly prominent. Traditional solutions rely on writing lengthy system prompts to "constrain" LLM behavior, but this approach is fragile and hard to maintain.

GuardPilot draws inspiration from the trending GitHub project [parlant](https://github.com/emcie-co/parlant) and takes an **independently developed** approach to provide a lighter, more flexible solution for Agent behavior compliance.

### 🌟 Key Differentiators

| Feature | GuardPilot | Other Solutions |
|---------|-----------|-----------------|
| **Deployment** | Pure CLI, zero GUI dependencies | Requires full server setup |
| **Rule Definition** | YAML-driven, clean and intuitive | Gherkin/complex DSL |
| **Dependencies** | Zero (Python stdlib only) | Multiple third-party libraries |
| **Chinese Support** | Native Chinese rules and reports | Primarily English |
| **Report Formats** | JSON / HTML / Markdown | Limited formats |
| **Conflict Detection** | Auto-detect and alert | Manual inspection required |

---

## ✨ Core Features

- 🎯 **YAML-Driven Rule Definition** — Define behavioral guidelines using clean YAML syntax with support for keyword, regex, pattern matching, and semantic similarity
- 🔍 **Multi-Dimensional Rule Matching** — Keyword matching, regular expressions, pattern matching, length checks, and semantic similarity (Jaccard)
- 📊 **Compliance Scoring System** — Automatic 0-100 compliance score with Block/Warning/Log severity levels
- 📋 **Multi-Format Reports** — JSON, HTML (dark theme), and Markdown report formats
- ⚠️ **Rule Conflict Detection** — Automatically detect logical conflicts between rules
- 🏷️ **Priority Management** — High/Medium/Low priority levels ensuring critical rules are evaluated first
- 🌐 **Bilingual Support** — Native support for both Chinese and English in rules, terminal output, and compliance reports
- 📦 **Built-in Rule Presets** — Four categories of preset rules: content safety, response format, domain compliance, and tone/style
- 🚀 **Zero External Dependencies** — Built entirely with Python standard library
- 🧪 **120 Unit Tests** — Comprehensive test coverage ensuring engine reliability

---

## 🚀 Quick Start

### 📋 Requirements

- **Python** >= 3.10 (no third-party dependencies needed)

### 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/gitstq/GuardPilot.git
cd GuardPilot

# Install (development mode)
pip install -e .
```

### 🎮 Usage

```bash
# 1. Initialize example rule files
guardpilot init

# 2. Validate rule file syntax
guardpilot validate guardpilot_rules.yaml

# 3. Check a single message
guardpilot check --rules guardpilot_rules.yaml --message "This is a test message"

# 4. Check a full conversation
guardpilot check --rules guardpilot_rules.yaml --conversation example_conversation.json

# 5. Generate compliance report (HTML format)
guardpilot report --rules guardpilot_rules.yaml --conversation example_conversation.json --format html

# 6. List all loaded rules
guardpilot rules list --rules guardpilot_rules.yaml
```

---

## 📖 Detailed Guide

### 📝 Rule File Format

Rule files use YAML format with the following structure:

```yaml
rules:
  - id: no-harmful-content
    name: No Harmful Content
    name_en: No Harmful Content
    description: Detect and block outputs containing harmful content
    category: content_safety
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value:
          - violence
          - explicit
          - gambling
        negate: false

  - id: max-response-length
    name: Max Response Length
    name_en: Max Response Length
    description: Limit maximum characters per response
    category: response_format
    priority: medium
    severity: warn
    enabled: true
    conditions:
      - type: length
        value: 2000
        operator: max

  - id: professional-tone
    name: Professional Tone
    name_en: Professional Tone
    description: Ensure output uses professional, polite language
    category: tone_style
    priority: low
    severity: log
    enabled: true
    conditions:
      - type: keyword
        value:
          - lol
          - wtf
          - omg
        negate: true
```

### 🎯 Condition Types

| Type | Description | Example |
|------|-------------|---------|
| `keyword` | Keyword matching | Detect if specific words exist/not exist |
| `regex` | Regular expression matching | Use regex to detect patterns |
| `pattern` | Predefined pattern matching | Email, phone, ID numbers, etc. |
| `length` | Length checking | Limit response max/min length |
| `custom` | Custom expression | Flexible custom matching logic |

### ⚡ Severity Levels

| Level | Description | Score Penalty |
|-------|-------------|---------------|
| `block` | **Blocking** — Serious violation, must be stopped | -20 points |
| `warn` | **Warning** — Issue that needs attention | -10 points |
| `log` | **Logging** — Minor issue, record only | -5 points |

### 📊 Compliance Scoring

GuardPilot automatically calculates a 0-100 compliance score:

- **90-100 (A)**: 🟢 Excellent — Fully compliant
- **70-89 (B)**: 🟡 Good — Minor issues present
- **50-69 (C)**: 🟠 Needs Improvement — Several issues present
- **0-49 (D)**: 🔴 Non-Compliant — Serious violations

### 📋 Built-in Rule Presets

GuardPilot includes four categories of preset rules ready to use:

```bash
# Use built-in rule presets
guardpilot check --rules guardpilot/rules/content_safety.yaml --message "test message"
guardpilot check --rules guardpilot/rules/response_format.yaml --message "test message"
guardpilot check --rules guardpilot/rules/domain_compliance.yaml --message "test message"
guardpilot check --rules guardpilot/rules/tone_style.yaml --message "test message"
```

---

## 💡 Design Philosophy & Roadmap

### 🏗️ Design Principles

1. **Zero-Dependency Philosophy** — Python standard library only, lowering deployment barriers and avoiding dependency conflicts
2. **YAML-Driven** — Rules separated from code, enabling non-technical users to manage rules easily
3. **Progressive Compliance** — Block/Warning/Log three-tier mechanism for flexible scenario handling
4. **Developer-Friendly** — Clear CLI output, rich report formats, comprehensive error messages

### 🔮 Roadmap

- [ ] **v1.1** — Context-aware rule matching across conversation messages
- [ ] **v1.2** — Web Dashboard for visual rule management
- [ ] **v1.3** — LLM API integration for semantic-level compliance detection (GPT/Claude/DeepSeek)
- [ ] **v2.0** — Hot-reload rule updates and version management
- [ ] **v2.1** — SDK for integration with other Python projects
- [ ] **v2.2** — Rule marketplace for community-shared rule templates

---

## 📦 Packaging & Deployment

### 💻 Local Development

```bash
# Clone the repository
git clone https://github.com/gitstq/GuardPilot.git
cd GuardPilot

# Install (development mode)
pip install -e .

# Run tests
python -m unittest discover -s tests

# Verify installation
guardpilot --version
```

### 🐍 Library Integration

```python
from guardpilot.engine import RuleEngine
from guardpilot.reporter import Reporter

# Load rules
engine = RuleEngine()
rules = engine.load_rules("guardpilot_rules.yaml")

# Check a message
result = engine.check_message("This is a test message", rules)

# Generate report
reporter = Reporter()
print(reporter.generate_markdown(result))
```

### 🐳 Docker Deployment

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -e .
ENTRYPOINT ["guardpilot"]
```

### 🔄 CI/CD Integration

```yaml
# GitHub Actions example
- name: Compliance Check
  run: |
    guardpilot check --rules rules.yaml --conversation output.json
    guardpilot report --rules rules.yaml --conversation output.json --format json > report.json
```

---

## 🤝 Contributing

We welcome all forms of contributions! Please follow these steps:

1. 🍴 Fork this repository
2. 🌿 Create a feature branch: `git checkout -b feature/amazing-feature`
3. ✅ Ensure all tests pass: `python -m unittest discover -s tests`
4. 📝 Commit your changes: `git commit -m "feat: add amazing feature"`
5. 🚀 Push the branch: `git push origin feature/amazing-feature`
6. 📮 Submit a Pull Request

### 📋 Commit Convention

Please follow the [Angular Commit Convention](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation update
- `refactor:` Code refactoring
- `test:` Test related
- `chore:` Build/tooling changes

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>
