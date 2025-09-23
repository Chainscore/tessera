import os
import sys

from py_ark_vrf import verify_ring

from jam.block import TicketEnvelope
from jam.utils.constants import X

from .errors import SafroleError, SafroleErrorCode


class Worker:
    PUBKEYS: list[bytes] | None = None

    @classmethod
    def init_worker(cls, pubkeys: list[bytes]):
        cls.PUBKEYS = pubkeys

    @classmethod
    def verify_ticket(cls, ticket: TicketEnvelope, entropy: bytes):
        print(f"[child pid={os.getpid()}] | argv={sys.argv} | [cpus={os.cpu_count()}]")
        if not cls.PUBKEYS:
            raise ValueError("Bandersnatch Keys cannot be None")

        message = X.TICKET.value + entropy + bytes([ticket.attempt])
        if not verify_ring(
            message,
            ticket.signature,
            cls.PUBKEYS,
            b""
        ):
            raise SafroleError(
                SafroleErrorCode.BAD_TICKET_PROOF,
                f"Ticket {ticket} VRF Proof is invalid",
            )