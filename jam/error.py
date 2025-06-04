from typing import Any
from tsrkit_types.enum import Enum
from enum import Enum as OGEnum


class JamError(Exception):
    def __init__(self, code: Enum | OGEnum, message = None, *args: Any) -> None:
        self.code = code
        # If no custom message is provided, default to the enum's value.
        if message is None:
            message = code.value
        self.message = message
        # Pass a formatted message to the base Exception.
        super().__init__(f"[{code.value}] {message}", *args)
