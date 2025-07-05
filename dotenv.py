"""Stub replacement for the external `python-dotenv` package.

This is *not* a full implementation – it merely provides the minimal
`load_dotenv` helper used inside `jam.__init__` such that importing Jam
modules in an environment without the real dependency does not fail.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_dotenv(_path: str | Path | None = None, *args: Any, **kwargs: Any) -> bool:  # noqa: D401, ANN401
    """No-op stand-in for `python-dotenv.load_dotenv`.

    Always returns ``True`` to signal success even though environment
    variables are *not* actually loaded in this stub.
    """

    # In local development most variables are already present or the user
    # supplies them via the shell.  Silently succeed so the caller can keep
    # running without caring whether dotenv support is available.
    return True