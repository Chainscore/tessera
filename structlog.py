"""Very small stub for the `structlog` dependency.

Provides the `get_logger()` helper used throughout the Jam codebase.
Each logger method is a no-op that simply returns the logger so that
chained calls like `logger.debug('msg', key=value)` do not fail.
"""

from __future__ import annotations

from typing import Any
import sys
import types


class _DummyLogger:
    def __getattr__(self, name: str):  # noqa: D401
        def _no_op(*args: Any, **kwargs: Any):  # noqa: ANN001
            return self
        return _no_op

    def bind(self, **kwargs: Any):  # noqa: D401
        return self


_logger = _DummyLogger()

# Core structlog public helpers ----------------------------------------------

def configure(*args, **kwargs):  # noqa: D401, ANN001
    # No-op configuration.
    return None


def get_logger(_name: str | None = None):  # noqa: D401
    return _logger


def make_filtering_bound_logger(_min_level):  # noqa: D401, ANN001
    # Return identity wrapper that ignores filtering.
    def _wrapper(logger):
        return logger
    return _wrapper

# submodule processors --------------------------------------------------------
processors_mod = types.ModuleType("structlog.processors")

class _TimeStamper:  # noqa: D401
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, *args, **kwargs):
        return args[-1] if args else {}

def _add_log_level(logger, name, event_dict):  # noqa: D401, ANN001
    event_dict.setdefault("level", name)
    return event_dict

class _JSONRenderer:  # noqa: D401
    def __call__(self, logger, name, event_dict):
        return str(event_dict)

setattr(processors_mod, "TimeStamper", _TimeStamper)
setattr(processors_mod, "add_log_level", _add_log_level)
setattr(processors_mod, "JSONRenderer", _JSONRenderer)

sys.modules["structlog.processors"] = processors_mod

# submodule stdlib ------------------------------------------------------------
stdlib_mod = types.ModuleType("structlog.stdlib")

class _LoggerFactory:  # noqa: D401
    def __call__(self, *args, **kwargs):
        return _logger

setattr(stdlib_mod, "LoggerFactory", _LoggerFactory)

sys.modules["structlog.stdlib"] = stdlib_mod

_dev = types.ModuleType("structlog.dev")

class _ConsoleRenderer:  # noqa: D401
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):  # noqa: D401, ANN001
        return ""

setattr(_dev, "ConsoleRenderer", _ConsoleRenderer)

sys.modules["structlog.dev"] = _dev