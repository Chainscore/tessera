from typing import Any
from tsrkit_types.enum import Enum
from enum import Enum as OGEnum

class JamErrorCode(Enum):
    INVALID_BLOCK = "Block is invalid"

class JamError(Exception):
    def __init__(self, code: Enum | OGEnum, message=None, *args: Any) -> None:
        self.code = code
        # If no custom message is provided, default to the enum's value.
        if message is None:
            message = code.value
        self.message = message
        # Pass a formatted message to the base Exception.
        super().__init__(f"[{code.value}] {message}", *args)

    def __reduce__(self):
        """
        Ensure that when the exception is unpickled, the constructor receives
        (code, message) so `code` is not replaced by the Exception.args string.
        """
        # Return (callable, args_tuple [, state]) — simple and reliable.
        return (self.__class__, (self.code, self.message))