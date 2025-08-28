"""Constants for the JAM protocol as defined in the specification."""

from tsrkit_types import Enum

from datetime import datetime, timezone
from jam.utils.chainspec import chain_config

# ───────────────────────────────────────
# Networking 
# ───────────────────────────────────────
GENESIS_HASH = "b5af8edad70d962097eefa2cef92c8284cf0a7578b70a6b7554cf53ae6d51222"
JAMNP_VERSION = "0"
NODE_ALPN = f"jamnp-s/{JAMNP_VERSION}/{GENESIS_HASH[:8]}" 

# ───────────────────────────────────────
# Constants (I.4.4, JAM Graypaper Order)
# ───────────────────────────────────────

# A — The period, in seconds, between audit tranches.
AUDIT_PERIOD = 8
A = AUDIT_PERIOD

# B_I — Additional minimum balance per item of elective service state.
ADDITIONAL_BALANCE_PER_ITEM = 10
B_I = ADDITIONAL_BALANCE_PER_ITEM

# B_L — Additional minimum balance per octet of elective service state.
ADDITIONAL_BALANCE_PER_OCTET = 1
B_L = ADDITIONAL_BALANCE_PER_OCTET

# B_S — Basic minimum balance which all services require.
BASIC_MINIMUM_BALANCE = 100
B_S = BASIC_MINIMUM_BALANCE

# C — The total number of cores.
CORE_COUNT = chain_config.num_cores  # e.g. 341
C = CORE_COUNT

# E — Length of an epoch, in timeslots.
EPOCH_LENGTH = chain_config.epoch_duration
E = EPOCH_LENGTH

# D — Timeslot count after which an unreferenced preimage may be expunged.
PREIMAGE_EVICTION_TIMESLOTS = 32  # TODO: 32 * EPOCH_LENGTH
D = PREIMAGE_EVICTION_TIMESLOTS

# F — Audit bias factor; expected # of additional validators who will audit due to prior no-show.
AUDIT_BIAS_FACTOR = 2
F = AUDIT_BIAS_FACTOR

# G_A — Gas allocated to invoke a work-report’s Accumulation logic.
ACCUMULATION_GAS = 10_000_000
G_A = ACCUMULATION_GAS

# G_I — Gas allocated to invoke a work-package’s Is-Authorized logic.
IS_AUTHORIZED_GAS = 50_000_000
G_I = IS_AUTHORIZED_GAS

# G_R — Gas allocated to invoke a work-package’s Refine logic.
REFINE_GAS = 5_000_000_000
G_R = REFINE_GAS

# G_T — Total gas allocated across all accumulation. Must satisfy: G_T ≥ G_A ⋅ C + Σ_gas(vkg)
TOTAL_GAS = 3_500_000_000
G_T = TOTAL_GAS

# H — Size of recent block history, in blocks.
RECENT_HISTORY_SIZE = 8
H = RECENT_HISTORY_SIZE

# I — Max number of work items in a package.
MAX_WORK_ITEMS = 16
I = MAX_WORK_ITEMS

# J — Max number of dependency items in a work-report.
MAX_DEPENDENCIES = 8
J = MAX_DEPENDENCIES

# K — Max number of tickets that can be submitted in a single extrinsic.
MAX_TICKETS_PER_EXTRINSIC = chain_config.max_tickets_per_extrinsic
K = MAX_TICKETS_PER_EXTRINSIC

# L — Max age (in timeslots) of the lookup anchor.
LOOKUP_ANCHOR_MAX_AGE = 14_400
L = LOOKUP_ANCHOR_MAX_AGE

# N — Ticket entries per validator.
TICKET_ENTRIES_PER_VALIDATOR = chain_config.tickets_per_validator
N = TICKET_ENTRIES_PER_VALIDATOR

# O — Max number of items in the authorizations pool.
MAX_AUTH_POOL_ITEMS = 8
O = MAX_AUTH_POOL_ITEMS

# P — Slot period in seconds.
SLOT_PERIOD = chain_config.slot_duration
P = SLOT_PERIOD

# Q — Max number of items in the authorizations queue.
MAX_AUTH_QUEUE_ITEMS = 80
Q = MAX_AUTH_QUEUE_ITEMS

# R — Rotation period of validator-core assignments, in timeslots.
ROTATION_PERIOD = chain_config.rotation_period
R = ROTATION_PERIOD

# S — Max entries in the accumulation queue.
MAX_ACCUMULATION_ENTRIES = 1024
S = MAX_ACCUMULATION_ENTRIES

# T — Max number of extrinsics in a work-package.
EXTRINSIC_COUNT = 128
T = EXTRINSIC_COUNT

# U — Timeslot period after which unavailable work may be replaced.
UNAVAILABLE_WORK_EXPIRY = 5
U = UNAVAILABLE_WORK_EXPIRY

# V — Total number of validators.
VALIDATOR_COUNT = chain_config.num_validators
V = VALIDATOR_COUNT

# W_A — Max size of is-authorized code (in octets).
MAX_AUTH_CODE_SIZE = 64_000
W_A = MAX_AUTH_CODE_SIZE

# W_B — Max encoded size of a work-package (extrinsics + imports), in octets.
MAX_ENCODED_WORK_PACKAGE_SIZE = 13_794_305
W_B = MAX_ENCODED_WORK_PACKAGE_SIZE

# W_C — Max size of service code, in octets.
MAX_SERVICE_CODE_SIZE = 4_000_000
W_C = MAX_SERVICE_CODE_SIZE

# W_E — Basic size of erasure-coded pieces (in octets). See equation H.6
BASIC_ERASURE_SIZE = 684
W_E = BASIC_ERASURE_SIZE

# W_G — Size of a segment in octets.
SEGMENT_SIZE = 4104  # = W_P * W_E
W_G = SEGMENT_SIZE

# W_M — Max number of imports in a work-package.
MAX_IMPORT_ITEM = 3072
W_M = MAX_IMPORT_ITEM

# W_P — Number of erasure-coded pieces in a segment.
ERASURE_PIECES_PER_SEGMENT = 6
W_P = ERASURE_PIECES_PER_SEGMENT

# W_R — Total size of all unbounded blobs in work-report (in octets).
MAX_WORK_REPORT_SIZE = 48 * 1024  # = 48 KiB
W_R = MAX_WORK_REPORT_SIZE

# W_T — Size of transfer memo in octets.
TRANSFER_MEMO_SIZE = 128
W_T = TRANSFER_MEMO_SIZE

# W_X — Max number of exports in a work-package.
MAX_EXPORT_ITEM = 3072
W_X = MAX_EXPORT_ITEM


# X — Context strings for signing.
class X(Enum):
    AVAILABLE = b"jam_available"  # Ed25519 Availability assurances
    BEEFY = b"jam_beefy"  # BLS MMR commitments
    ENTROPY = b"jam_entropy"  # On-chain entropy randomness
    FALLBACK = b"jam_fallback_seal"  # Bandersnatch fallback block seal
    GUARANTEE = b"jam_guarantee"  # Ed25519 Guarantee statements
    ANNOUNCE = b"jam_announce"  # Ed25519 Audit announcements
    TICKET = b"jam_ticket_seal"  # RingVRF ticket gen / sealing
    AUDIT = b"jam_audit"  # Bandersnatch Audit selection entropy
    VALID = b"jam_valid"  # Ed25519 valid work-report judgments
    INVALID = b"jam_invalid"  # Ed25519 invalid work-report judgments


# Y — Number of slots into an epoch where ticket submission ends.
TICKET_SUBMISSION_END = chain_config.ticket_submission_end
Y = TICKET_SUBMISSION_END

# Z_A — PVM dynamic address alignment factor. See equation A.18
PVM_ADDR_ALIGNMENT = 2

# Z_I — PVM program init input data size. See A.7
PVM_INIT_DATA_SIZE = 2**24

# Z_P — PVM memory page size. See equation 4.24
PVM_MEMORY_PAGE_SIZE = 2**12

# Z_Z — PVM init zone size. See A.7
PVM_INIT_ZONE_SIZE = 2**16

# Z_R — Number of registers in the standard PVM
REGISTER_COUNT = 13


# ======= #
VALIDATORS_SUPER_MAJORITY = 1 + 2 * VALIDATOR_COUNT // 3
VALIDATORS_WONKY = VALIDATOR_COUNT // 3
GENESIS_TS = 1735732800  # January 1, 2025 12:00 UTC


# Jam Common‐Era epoch (2025-01-01 12:00 UTC)
JCE_EPOCH = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)

# T — current seconds since JCE_EPOCH
CURRENT_TIME = lambda: int((datetime.now(timezone.utc) - JCE_EPOCH).total_seconds())
