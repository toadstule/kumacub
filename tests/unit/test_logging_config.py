#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Test logging configuration behavior."""

from __future__ import annotations

import logging
import typing
from unittest import mock

import pytest
import structlog
from structlog.testing import capture_logs

from kumacub.logging_config import DEFAULT_LEVEL, configure_logging


@pytest.fixture(autouse=True)
def isolate_logging() -> typing.Iterator[None]:
    """Reset logging and structlog before and after each test."""
    logging.root.handlers = []
    structlog.reset_defaults()
    yield
    logging.root.handlers = []
    structlog.reset_defaults()


def _assert_logging_configured(expected_level: int, *, structured: bool = False) -> None:
    """Verify logging configuration.

    Args:
        expected_level: Expected log level
        structured: Whether to verify structured logging
    """
    # Verify root logger has a handler
    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert root.level == expected_level

    # Verify structlog is configured
    assert structlog.is_configured()

    if structured:
        # Verify structured logging output
        logger = structlog.get_logger()
        with capture_logs() as cap_logs:
            logger.info("test message", key="value")

        assert len(cap_logs) == 1
        log_entry = cap_logs[0]
        assert log_entry["event"] == "test message"


def test_configure_logging_defaults() -> None:
    """Test logging configuration with default parameters."""
    with mock.patch("logging.StreamHandler"):
        configure_logging()
        _assert_logging_configured(logging.getLevelName(DEFAULT_LEVEL.upper()))


def test_configure_logging_console() -> None:
    """Test console logging configuration."""
    with mock.patch("logging.StreamHandler"):
        configure_logging(level="DEBUG", structured=False)
        _assert_logging_configured(logging.DEBUG, structured=False)


def test_configure_logging_structured() -> None:
    """Test structured (JSON) logging configuration."""
    with mock.patch("logging.StreamHandler"):
        configure_logging(level="INFO", structured=True)
        _assert_logging_configured(logging.INFO, structured=True)


def test_configure_logging_custom_levels() -> None:
    """Test logging configuration with different log levels."""
    test_cases = [
        ("DEBUG", logging.DEBUG),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
        ("invalid", logging.INFO),  # Default to INFO for invalid levels
    ]

    with mock.patch("logging.StreamHandler"):
        for level_str, expected_level in test_cases:
            configure_logging(level=level_str, structured=True)
            root = logging.getLogger()
            assert root.level == expected_level


def test_configure_logging_third_party_loggers() -> None:
    """Test that third-party loggers are properly configured."""
    third_party_loggers = [
        "apscheduler",
        "httpx",
    ]

    configure_logging(level="DEBUG", structured=True)

    for name in third_party_loggers:
        logger = logging.getLogger(name)
        assert logger.level == logging.DEBUG


def test_configure_logging_reset() -> None:
    """Test that configure_logging resets previous configuration."""
    with mock.patch("logging.StreamHandler"):
        # First configuration
        configure_logging(level="DEBUG", structured=True)
        root1 = logging.getLogger()
        assert len(root1.handlers) == 1
        assert root1.level == logging.DEBUG

        # Second configuration
        configure_logging(level="WARNING", structured=False)
        root2 = logging.getLogger()
        # Should have only one handler (previous one was cleared)
        assert len(root2.handlers) == 1
        assert root2.level == logging.WARNING
