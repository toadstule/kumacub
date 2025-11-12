#  KumaCub - Run local checks; push results to Uptime Kuma.
# Copyright (c) 2025.

"""Application mapper package."""

from . import nagios  # noqa: F401 - ensure registration side-effect
from .result_translator import ResultTranslator, get_result_translator, translate  # re-export base API

__all__ = [
    "ResultTranslator",
    "get_result_translator",
    "translate",
]
