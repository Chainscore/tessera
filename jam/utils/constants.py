"""Constants for the JAM protocol as defined in the specification."""
from jam.chainspec import chain_config

# Time constants
AUDIT_PERIOD = 8  # seconds between audit tranches
SLOT_PERIOD = chain_config.slot_duration  # seconds
EPOCH_LENGTH = chain_config.epoch_duration  # timeslots
ROTATION_PERIOD = chain_config.rotation_period  # timeslots for validator-core assignments
LOOKUP_ANCHOR_MAX_AGE = 14_400  # maximum age in timeslots
TICKET_SUBMISSION_END = chain_config.ticket_submission_end  # slots into epoch
UNAVAILABLE_WORK_EXPIRY = 5  # timeslots
CONTEST_DURATION = chain_config.contest_duration

# Balance constants
BASIC_MINIMUM_BALANCE = 100
ADDITIONAL_BALANCE_PER_ITEM = 10
ADDITIONAL_BALANCE_PER_OCTET = 1

# Core and validator constants
CORE_COUNT = chain_config.num_cores
VALIDATOR_COUNT = chain_config.num_validators
TICKET_ENTRIES_PER_VALIDATOR = chain_config.tickets_per_validator
AUDIT_BIAS_FACTOR = 2
VALIDATORS_SUPER_MAJORITY = 2 * VALIDATOR_COUNT // 3 + 1

# Gas constants
ACCUMULATION_GAS = 10_000_000
IS_AUTHORIZED_GAS = 50_000_000
REFINE_GAS = 5_000_000_000
TOTAL_GAS = 3_000_000_000

# Size and count limits
MAX_WORK_ITEMS = 4
MAX_DEPENDENCIES = 8
MAX_TICKETS_PER_EXTRINSIC = chain_config.max_tickets_per_extrinsic
MAX_AUTH_POOL_ITEMS = 8
MAX_AUTH_QUEUE_ITEMS = 80
MAX_ACCUMULATION_ENTRIES = 1024
RECENT_HISTORY_SIZE = 8

# Memory and storage constants
PVM_ADDR_ALIGNMENT = 2
PVM_INIT_DATA_SIZE = 2**8
PVM_MEMORY_PAGE_SIZE = 2**12
PVM_INIT_ZONE_SIZE = 2**16
MAX_SERVICE_CODE_SIZE = 4_000_000  # octets
BASIC_ERASURE_SIZE = 684  # octets
SEGMENT_SIZE = 4104  # octets
MAX_MANIFEST_ENTRIES = 2**11
ERASURE_PIECES_PER_SEGMENT = 6
MAX_WORK_REPORT_SIZE = 48 * 2**10  # octets
TRANSFER_MEMO_SIZE = 128  # octets

# Signing context strings
SIGNING_CONTEXTS = {
    'available': '$jam_available',     # Ed25519 Availability assurances
    'beefy': '$jam_beefy',            # BLS Accumulate-result-root-MMR commitment
    'entropy': '$jam_entropy',         # On-chain entropy generation
    'fallback_seal': '$jam_fallback_seal',  # Bandersnatch Fallback block seal
    'guarantee': '$jam_guarantee',     # Ed25519 Guarantee statements
    'announce': '$jam_announce',       # Ed25519 Audit announcement statements
    'ticket_seal': '$jam_ticket_seal', # Bandersnatch RingVRF Ticket generation/block seal
    'audit': '$jam_audit',            # Bandersnatch Audit selection entropy
    'valid': '$jam_valid',            # Ed25519 Judgments for valid work-reports
    'invalid': '$jam_invalid',        # Ed25519 Judgments for invalid work-reports
}

# Maximum number of judgements per dispute
MAX_JUDGEMENTS_PER_DISPUTE = 32
