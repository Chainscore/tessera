from typing import Self
from jam.models.protocol.ticket import TicketBody
from jam.utils.constants import EPOCH_LENGTH, TICKET_SUBMISSION_END
from jam.utils.util_fns import outside_in
from tsrkit_types import U64, TypedArray, Option, Null
from jam.models.state.sigma import Sigma


class TicketsMarkData(TypedArray[TicketBody, EPOCH_LENGTH]):
    ...


class TicketsMark(Option[TicketsMarkData]):
    """Fixed-length array of ticket bodies."""

    @classmethod
    def produce(cls, state: Sigma, slot: U64) -> Self:
        """
        Returns the ticket.py markers for the given state
        https://graypaper.fluffylabs.dev/#/68eaa1f/0e82030e8203?v=0.6.4
        - Ensure we have exact EPOCH_LENGTH ticket.py accumulated
        - Ticket collection phase is just getting over (m < TICKET_SUBMISSION_END <= m')
        - We have to be in the same epoch
        """
        if (
            (len(state.gamma.a) == EPOCH_LENGTH)
            and
            (state.tau % EPOCH_LENGTH < TICKET_SUBMISSION_END <= slot % EPOCH_LENGTH)
            and
            (int(slot // EPOCH_LENGTH) == int(state.tau // EPOCH_LENGTH))
        ):
            return cls(TicketsMarkData(outside_in(state.gamma.a)))
        else:
            return cls(Null)
