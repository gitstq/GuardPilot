# Contributing to GuardPilot

Thank you for your interest in contributing to GuardPilot! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- No external dependencies required (stdlib only)

### Setup

1. Clone the repository
2. Create a virtual environment (optional but recommended)
3. Install the package in development mode:

```bash
pip install -e .
```

### Running Tests

```bash
python -m pytest tests/
```

Or using unittest directly:

```bash
python -m unittest discover -s tests -v
```

## Development Guidelines

### Code Style

- Follow PEP 8 conventions
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- All functions and classes must have docstrings
- Code comments should be in English
- User-facing messages should support both English and Chinese

### Project Structure

```
guardpilot/
  guardpilot/
    __init__.py      # Package init with version
    cli.py           # CLI entry point
    engine.py        # Core rule engine
    models.py        # Data models
    reporter.py      # Report generators
    utils.py         # Utility functions
    templates.py     # Built-in templates
    rules/           # Built-in rule presets
  tests/             # Test suite
  pyproject.toml     # Project configuration
```

### Adding New Rules

1. Create a new YAML file in `guardpilot/rules/`
2. Follow the existing rule format with id, name, description, category, priority, conditions, severity, and enabled fields
3. Add tests for the new rules in `tests/`
4. Update documentation

### Adding New Report Formats

1. Add a new `generate_*` method to the `Reporter` class in `reporter.py`
2. Add the format option to the CLI in `cli.py`
3. Add tests in `tests/test_reporter.py`

### Commit Messages

Use conventional commit format:

```
type(scope): description

feat(engine): add new pattern matching condition
fix(cli): resolve argument parsing issue
docs: update contributing guide
test(engine): add tests for conflict detection
refactor(utils): improve YAML parser performance
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes with appropriate tests
4. Ensure all tests pass
5. Submit a pull request with a clear description

## Reporting Issues

When reporting issues, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output or error messages

## License

By contributing to GuardPilot, you agree that your contributions will be licensed under the MIT License.
