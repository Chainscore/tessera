"""Constants used by the JAM fuzzer target.

Keep protocol tags and small lightweight constants in one place so the
implementation code stays focused on behavior.
"""

# ASN.1 Tags for the JAM Fuzzing Protocol v1
# Based on fuzz-v1.asn Message CHOICE tags
TAG_PEER_INFO = 0      # peer-info [0]
TAG_INITIALIZE = 1     # initialize [1] 
TAG_STATE_ROOT = 2     # state-root [2]
TAG_IMPORT_BLOCK = 3   # import-block [3]
TAG_GET_STATE = 4      # get-state [4]
TAG_STATE = 5          # state [5]
TAG_ERROR = 255        # error [255]

# Feature constants for PeerInfo negotiation
FEATURE_ANCESTRY = 1   # 2^0 - Target has access to block ancestry
FEATURE_FORK = 2       # 2^1 - Simple forking support
FEATURE_RESERVED = 2147483648  # 2^31 - Reserved for future extensions

__all__ = [
    "TAG_PEER_INFO",
    "TAG_INITIALIZE", 
    "TAG_STATE_ROOT",
    "TAG_IMPORT_BLOCK",
    "TAG_GET_STATE",
    "TAG_STATE",
    "TAG_ERROR",
    "FEATURE_ANCESTRY",
    "FEATURE_FORK", 
    "FEATURE_RESERVED",
]
