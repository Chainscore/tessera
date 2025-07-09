VERSION=1

from jam.utils.constants import (
    BASIC_MINIMUM_BALANCE,  # B_S
    ADDITIONAL_BALANCE_PER_ITEM,  # B_I
    ADDITIONAL_BALANCE_PER_OCTET,  # B_L
    PREIMAGE_EVICTION_TIMESLOTS,  # D
    EPOCH_LENGTH,  # E
    ACCUMULATION_GAS,  # G_A
    IS_AUTHORIZED_GAS,  # G_I
    REFINE_GAS,  # G_R
    TOTAL_GAS,  # G_T
    RECENT_HISTORY_SIZE,  # H
    MAX_WORK_ITEMS,  # I
    MAX_DEPENDENCIES,  # J
    MAX_TICKETS_PER_EXTRINSIC,  # K
    LOOKUP_ANCHOR_MAX_AGE,  # L
    TICKET_ENTRIES_PER_VALIDATOR,  # N
    MAX_AUTH_POOL_ITEMS,  # O
    MAX_AUTH_QUEUE_ITEMS,  # Q
    ROTATION_PERIOD,  # R
    EXTRINSIC_COUNT,  # T
    UNAVAILABLE_WORK_EXPIRY,  # U
    VALIDATOR_COUNT,  # V
    MAX_ENCODED_WORK_PACKAGE_SIZE,  # W_B
    MAX_SERVICE_CODE_SIZE,  # W_C
    BASIC_ERASURE_SIZE,  # W_E
    MAX_IMPORT_ITEM,  # W_M
    MAX_AUTH_CODE_SIZE,  # W_A
    MAX_EXPORT_ITEM,  # W_X
)

params = {
    # Canonical JAM parameters
    "deposit_per_account": BASIC_MINIMUM_BALANCE,  # B_S
    "deposit_per_item": ADDITIONAL_BALANCE_PER_ITEM,  # B_I
    "deposit_per_byte": ADDITIONAL_BALANCE_PER_OCTET,  # B_L
    "min_turnaround_period": PREIMAGE_EVICTION_TIMESLOTS,  # D
    "epoch_period": EPOCH_LENGTH,  # E
    "max_accumulate_gas": ACCUMULATION_GAS,  # G_A
    "max_is_authorized_gas": IS_AUTHORIZED_GAS,  # G_I
    "max_refine_gas": REFINE_GAS,  # G_R
    "block_gas_limit": TOTAL_GAS,  # G_T
    "recent_block_count": RECENT_HISTORY_SIZE,  # H
    "max_work_items": MAX_WORK_ITEMS,  # I
    "max_dependencies": MAX_DEPENDENCIES,  # J
    "max_tickets_per_block": MAX_TICKETS_PER_EXTRINSIC,  # K
    "max_lookup_anchor_age": LOOKUP_ANCHOR_MAX_AGE,  # L
    "tickets_attempts_number": TICKET_ENTRIES_PER_VALIDATOR,  # N
    "auth_window": MAX_AUTH_POOL_ITEMS,  # O
    "auth_queue_len": MAX_AUTH_QUEUE_ITEMS,  # Q
    "rotation_period": ROTATION_PERIOD,  # R
    "max_extrinsics": EXTRINSIC_COUNT,  # T
    "availability_timeout": UNAVAILABLE_WORK_EXPIRY,  # U
    "val_count": VALIDATOR_COUNT,  # V
    "max_input": MAX_ENCODED_WORK_PACKAGE_SIZE,  # W_B
    "max_refine_code_size": MAX_SERVICE_CODE_SIZE,  # W_C
    "basic_piece_len": BASIC_ERASURE_SIZE,  # W_E
    "max_imports": MAX_IMPORT_ITEM,  # W_M
    # Additional parameters
    "max_is_authorized_code_size": MAX_AUTH_CODE_SIZE,  # W_A
    "max_exports": MAX_EXPORT_ITEM,  # W_X
    "max_refine_memory": None,  # Not defined in constants.py
    "max_is_authorized_memory": None,  # Not defined in constants.py
}
