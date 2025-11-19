#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Translators between pipeline stages.

This module provides translation functions between the output of one stage and the input args of the next.
Contributors can add new translators here when implementing new executors, parsers, or publishers.
"""

import textwrap
import typing

import pydantic

from kumacub.domain import models
from kumacub.infrastructure import executors, parsers, publishers


def executor_to_parser(
    executor_output: pydantic.BaseModel,
    executor_name: str,
    parser_name: str,
    check_id: str,
) -> pydantic.BaseModel:
    """Translate executor output to parser args.

    To add a new translator:
    1. Add a new case matching (executor name, parser name)
    2. Return the appropriate parser args model

    Args:
        executor_output: Output from any executor
        executor_name: Name of the executor that produced the output
        parser_name: Name of the target parser
        check_id: Check identifier for logging

    Returns:
        Parser-specific args model

    Raises:
        ValueError: If no translator exists for this combination
    """
    match (executor_name, parser_name):
        case ("process", "nagios"):
            output = typing.cast("executors.ProcessExecutorOutput", executor_output)
            return parsers.NagiosParserArgs(
                id=check_id,
                output=output.stdout or output.stderr,
                exit_code=output.exit_code,
            )
        case _:
            msg = f"No translator for {executor_name} executor -> {parser_name} parser"
            raise ValueError(msg)


def parser_to_publisher(
    parser_output: pydantic.BaseModel,
    parser_name: str,
    publisher_name: str,
    check: models.Check,
    ping: float | None = None,
) -> pydantic.BaseModel:
    """Translate parser output to publisher args.

    To add a new translator:
    1. Add a new case matching (parser name, publisher name)
    2. Return the appropriate publisher args model

    Args:
        parser_output: Output from any parser
        parser_name: Name of the parser that produced the output
        publisher_name: Name of the target publisher
        check: The check being executed (for publisher-specific fields)
        ping: Optional ping time in milliseconds

    Returns:
        Publisher-specific args model

    Raises:
        ValueError: If no translator exists for this combination
    """
    match (parser_name, publisher_name):
        case ("nagios", "stdout"):
            output = typing.cast("parsers.NagiosParserOutput", parser_output)
            max_msg_len = publishers.StdoutPublishArgs.model_fields["msg"].metadata[0].max_length
            return publishers.StdoutPublishArgs(
                id=check.name,
                status="up" if output.exit_code == 0 else "down",
                msg=textwrap.shorten(output.service_output, width=max_msg_len, placeholder="..."),
            )
        case ("nagios", "uptime_kuma"):
            output = typing.cast("parsers.NagiosParserOutput", parser_output)
            max_msg_len = publishers.UptimeKumaPublishArgs.model_fields["msg"].metadata[0].max_length
            return publishers.UptimeKumaPublishArgs(
                id=check.name,
                url=check.publisher.url,
                push_token=check.publisher.push_token,
                status="up" if output.exit_code == 0 else "down",
                msg=textwrap.shorten(output.service_output, width=max_msg_len, placeholder="..."),
                ping=ping,
            )
        case _:
            msg = f"No translator for {parser_name} parser -> {publisher_name} publisher"
            raise ValueError(msg)
