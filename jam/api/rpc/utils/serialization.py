"""
Serialization Utilities

Centralized serialization/deserialization for JSON-RPC protocol.
"""

import base64
import json
from typing import Any, Union, Type
from tsrkit_types.itf.codable import Codable
from jam.api.rpc.types import RpcError

# TODO: REMOVE LATER
# BYPASS FOR MANUAL TESTING WITH OLDER RPC EXPLORER
# Serialization mode: "list" -> list(val), "b64" -> base64 encoded string
# Set by RPCService based on port (19801 = list, others = b64)
_serialize_mode: str = "b64"


def set_serialize_mode(mode: str) -> None:
    """Set the serialization mode for byte encoding."""
    global _serialize_mode
    _serialize_mode = mode


def b64(val: Union[bytes, bytearray, list[int], None]) -> Union[str, list[int], None]:
    """Encode bytes to base64 string or int list depending on mode."""
    if val is None:
        return None
    if isinstance(val, list):
        val = bytes(val)
    if _serialize_mode == "list":
        return list(val)
    return base64.b64encode(val).decode("ascii")


def unb64(val: Union[str, bytes, list[int]]) -> bytes:
    """Decode base64 string to bytes."""
    if isinstance(val, bytes):
        return val
    if isinstance(val, list):
        try:
            return bytes(val)
        except Exception:
            raise RpcError(-32602, "Invalid byte list")
    if isinstance(val, str):
        try:
            return base64.b64decode(val, validate=True)
        except Exception:
            raise RpcError(-32602, "Invalid base64 input")
    raise RpcError(-32602, "Invalid base64 input type")


def parse_params(types: list[Type[Codable]], params: list) -> list:
    """Parse received RPC parameters to expected types."""
    if not isinstance(params, list):
        raise RpcError(-32602, "Params must be an array")

    if len(types) != len(params):
        raise RpcError(-32602, "Invalid params length")

    out = []
    for typ, raw in zip(types, params):
        try:
            if isinstance(raw, str):
                raw = unb64(raw)
            elif isinstance(raw, list):
                raw = bytes(raw)
            elif isinstance(raw, bool):
                pass
            elif isinstance(raw, (int, float)):
                raw = int(raw)
            elif isinstance(raw, (bytes, bytearray)):
                pass
            else:
                raise RpcError(-32602, f"Invalid parameter for {typ}")

            out.append(typ(raw))

        except RpcError:
            raise
        except Exception as e:
            raise RpcError(-32602, f"Cannot parse {raw!r} as {typ.__name__}: {e}")

    return out


def json_default(val: Any) -> Any:
    """
    JSON default serializer for non-standard types.
    Recursively handles nested structures.
    """
    # None → None (explicit check)
    if val is None:
        return None

    # Primitive Types
    if isinstance(val, bool):
        return val

    if isinstance(val, int):
        return int(val)

    if isinstance(val, (float, str)):
        return val


    # Bytes → base64
    if isinstance(val, (bytes, bytearray)):
        return b64(val)

    # List/Tuple → recurse into items
    if isinstance(val, (list, tuple)):
        return [json_default(item) for item in val]

    # Struct Objects with encode method
    if isinstance(val, Codable):
        try:
            encoded = val.encode()
            return b64(encoded)
        except Exception:
            return str(val)

    # Dict → recurse into values
    if isinstance(val, dict):
        return {k: json_default(v) for k, v in val.items()}

    # Fallback
    return str(val)

def dumps(data: Any) -> str:
    """Serialize data to JSON string."""
    return json.dumps(data, default=json_default)
