from tsrkit_types.enum import Enum
from jam.error import JamError

class SafroleError(JamError):
    ...

class SafroleErrorCode(Enum):
    """Error codes for the Safrole consensus protocol."""

    BAD_SLOT = "bad_slot"  # Invalid slot number
    UNEXPECTED_TICKET = "unexpected_ticket"  # Ticket received when not expected
    BAD_TICKET_ORDER = "bad_ticket_order"  # Tickets not in sorted order by VRF output
    BAD_TICKET_PROOF = "bad_ticket_proof"  # Invalid VRF proof for ticket
    BAD_TICKET_ATTEMPT = "bad_ticket_attempt"  # Invalid ticket attempt index
    RESERVED = "reserved"  # Reserved for future use
    DUPLICATE_TICKET = "duplicate_ticket"  # Duplicate ticket submission
    
    #Custom for equ 6.30
    BAD_TICKET_COUNT = "bad_ticket_count"  # Invalid ticket count 
