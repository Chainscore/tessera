# """Ticket types for the JAM protocol."""
# from dataclasses import dataclass
# from typing import List, Union
# from .base import U8
# from .core import OpaqueHash
# from .crypto import BandersnatchRingVrfSignature, BandersnatchPublic

# TicketId = OpaqueHash
# TicketAttempt = U8

# @dataclass
# class TicketEnvelope:
#     """Ticket envelope structure."""
#     attempt: TicketAttempt
#     signature: BandersnatchRingVrfSignature

# @dataclass
# class TicketBody:
#     """Ticket body structure."""
#     id: TicketId
#     attempt: TicketAttempt

# @dataclass
# class TicketsAccumulator:
#     """Tickets accumulator structure."""
#     tickets: List[TicketBody]

#     def __post_init__(self):
#         # epoch_length should be imported from constants
#         if len(self.tickets) > 0:  # epoch_length
#             raise ValueError("TicketsAccumulator exceeds epoch length")

# @dataclass
# class TicketsOrKeys:
#     """Tickets or keys structure."""
#     value: Union[List[TicketBody], List[BandersnatchPublic]]
#     is_tickets: bool = True

#     def __post_init__(self):
#         # epoch_length should be imported from constants
#         if len(self.value) > 0:  # epoch_length
#             raise ValueError("TicketsOrKeys exceeds epoch length")

# @dataclass
# class TicketsExtrinsic:
#     """Tickets extrinsic structure."""
#     tickets: List[TicketEnvelope]

#     def __post_init__(self):
#         if len(self.tickets) > 16:
#             raise ValueError("TicketsExtrinsic cannot contain more than 16 tickets") 