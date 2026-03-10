"""
Chain Handler

Handlers for chain-related RPC methods.
"""
from jam.block import Block
from jam.api.rpc.handlers.base import BaseHandler
from jam.api.rpc.utils.serialization import parse_params
from jam.state.state import State
from jam.types import TimeSlot
from jam.types.protocol.crypto import HeaderHash
from jam.utils.constants import CURRENT_TIME, SLOT_PERIOD


class ChainHandler(BaseHandler):
    """Handler for chain-related RPC methods."""

    @staticmethod
    def parameters(_) -> dict:
        """Returns the chain parameters."""
        from jam.api.rpc.parameters import parameters

        return {"V1": parameters}

    def best_block(self, _) -> dict:
        """Returns the header hash and slot of the head of the best chain."""
        block = self.grandpa.load_best()
        return {
            "header_hash": block.header.hash(),
            "slot": block.header.slot,
        }

    def finalized_block(self, _) -> dict:
        """Returns the header hash and slot of the latest finalized block."""
        block = self.grandpa.load_final()
        return {
            "header_hash": block.header.hash(),
            "slot": block.header.slot,
        }

    def parent(self, params: list) -> dict | None:
        """Returns the parent of the block with the given header hash."""
        (header_hash,) = parse_params([HeaderHash], params)
        block = Block.load(header_hash, self.main_db)

        if not block or not block.header.parent:
            return None

        parent = block.load_parent(self.main_db)
        return {
            "header_hash": block.header.parent,
            "slot": int(parent.header.slot),
        }

    def state_root(self, params: list) -> bytes:
        """Returns the posterior state root of the block."""
        (header_hash,) = parse_params([HeaderHash], params)
        state = State.load(self.jam, header_hash)
        return state.root

    def beefy_root(self, params: list) -> bytes | None:
        """Returns the BEEFY root of the block."""
        (header_hash,) = parse_params([HeaderHash], params)
        state = State.load(self.jam, header_hash)

        for item in state.beta.h:
            if item.header_hash == header_hash:
                return item.beefy_root

        return None

    def statistics(self, params: list) -> bytes:
        """Returns the activity statistics stored in the posterior state."""
        (header_hash,) = parse_params([HeaderHash], params)
        state_at = State.load(self.jam, header_hash)
        return state_at.pi.encode()

    def sync_state(self, _) -> dict:
        """Returns the sync state of the node."""
        node = self.router.node
        state = self.state
        curr_slot = CURRENT_TIME() // SLOT_PERIOD

        return {
            "num_peers": len(node.all_connected),
            "status": "Completed" if state.tau == curr_slot else "InProgress",
        }

    def sync_status(self, _) -> str:
        """Returns just the sync status string"""
        state = self.state
        curr_slot = CURRENT_TIME() // SLOT_PERIOD
        return "Completed" if state.tau == curr_slot else "InProgress"

    # TODO: handle block request by explorer.
    def block_request_handler(self, params: list):
        settings = self.settings

        identifier = params[0]
        by = params[1] if len(params) > 1 else "hash"
        try:
            if by == "slot":
                block = Block.load_w_ts(TimeSlot(identifier), settings.main_db)
                if isinstance(block, list):
                    block = block[0]
            else:
                hh = HeaderHash(bytes(identifier))
                block = Block.load(hh, settings.main_db)
            if block is None:
                return None
            return block
        except Exception:
            return None