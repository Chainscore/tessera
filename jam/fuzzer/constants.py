"""Constants used by the JAM fuzzer target.

Keep protocol tags and small lightweight constants in one place so the
implementation code stays focused on behavior.
"""

# ASN.1 Tags for the JAM Fuzzing Protocol
TAG_PEER_INFO = 0
TAG_IMPORT_BLOCK = 1
TAG_SET_STATE = 2
TAG_GET_STATE = 3
TAG_STATE = 4
TAG_STATE_ROOT = 5

__all__ = [
    "TAG_PEER_INFO",
    "TAG_IMPORT_BLOCK",
    "TAG_SET_STATE",
    "TAG_GET_STATE",
    "TAG_STATE",
    "TAG_STATE_ROOT",
]
