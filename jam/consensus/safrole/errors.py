from jam.types.base.enum import Enum, decodable_enum

@decodable_enum
class SafroleError(Enum):
    BAD_SLOT = "bad_slot"
    UNEXPECTED_TICKET = "unexpected_ticket"
    BAD_TICKET_ORDER = "bad_ticket_order"
    BAD_TICKET_PROOF = "bad_ticket_proof"
    BAD_TICKET_ATTEMPT = "bad_ticket_attempt"
    RESERVED = "reserved"
    DUPLICATE_TICKET = "duplicate_ticket"