# Contributing to KumaCub

Thank you for your interest in contributing to KumaCub! We welcome all contributions, including bug reports, feature requests, documentation improvements, and code contributions.

## Getting Started

### Prerequisites

- Python 3.11 - 3.14
- [uv](https://github.com/astral-sh/uv) (Python package/project manager)
- Git

### Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone git@github.com:your-username/kumacub.git
   cd kumacub
   ```
3. Install development dependencies:
   ```bash
   make dep
   source .venv/bin/activate
   ```
4. Install the package in development mode:
   ```bash
   make dev
   ```

### Project Structure

```
kumacub/
├── src/kumacub/
│   ├── application/
│   │   └── services/
│   │       ├── runner.py            # Check execution orchestration
│   │       ├── translators.py       # Result translators
│   │       └── daemon.py            # Main daemon service for scheduled checks
│   ├── data/
│   │   └── config.toml              # Example configuration
│   │   └── kumacub.service          # Systemd unit file
│   ├── domain/
│   │   └── models.py                # Core domain models
│   ├── infrastructure/
│   │   ├── executors/
│   │   │   └── process_executor.py  # Process execution
│   │   ├── parsers/
│   │   │   └── nagios.py            # Nagios output parsing
│   │   └── publishers/
│   │       └── stdout.py            # Stdout integration
│   │       └── uptime_kuma.py       # Uptime Kuma integration
│   ├── entrypoints/
│   │   └── cli.py                   # Comand line interface
│   ├── config.py                    # Configuration management
│   └── logging_config.py            # Logging setup
├── tests/
│   └── unit/                        # Unit tests
└── README.md
```

## Development Workflow

### Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-number-description
   ```

2. Make your changes following the [code style](#code-style) guidelines.

3. Run formatter, linters and tests and checks:
   ```bash
   make format check
   ```

4. Commit your changes with a high-quality commit message.


### Code Style

We use `ruff` and `mypy` for linting and formatting. To check and fix code style:

```bash
make format  # Auto-format code
make lint    # Check for linting errors
```

Key style guidelines:
- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code
- In general follow [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) for Python code
- Use type hints for all functions and methods
- Include docstrings for all public modules, classes, and functions
- Keep lines under 120 characters

## Submitting Changes

1. Push your changes to your fork:
   ```bash
   git push origin your-branch-name
   ```

2. Open a pull request against the `main` branch.

### Pull Request Guidelines

- Keep pull requests focused on a single feature or bug fix
- Include tests for new features and bug fixes
- Update documentation as needed
- Ensure all tests pass and code coverage remains at least 90%
- Reference any related issues in your PR description

## Reporting Issues

When reporting issues, please include:

1. A clear, descriptive title
2. Steps to reproduce the issue
3. Expected vs. actual behavior
4. Environment details (OS, Python version, etc.)
5. Any relevant logs or error messages

## License

By contributing to KumaCub, you agree that your contributions will be licensed under the [GNU General Public License v3.0](LICENSE).
