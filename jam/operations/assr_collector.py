from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jam.logging import get_logger
from jam.network.protocols.ce_141 import AssuranceDistribution
from jam.utils.constants import CORE_COUNT
from tsrkit_types import Bytes
from typing import List 

logger = get_logger("nodeops")

class AssuranceCollector:
    _collected: List[bool]

    def __init__(self) -> None:
        self._collected = []

    def record_shard(self, core_index: int):
        self._collected[core_index] = True 
        logger.debug("Recorded shard for core", core_index=core_index)
    
    async def run(self, time_slot: int):
        from jam.settings import settings
        signr = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private).sign(
            Bytes.from_bits(self._collected)
        )
        logger.info("Distributing Assurance", time_slot=time_slot, signature=signr.hex()[:16] + "...")
        
        # TODO: Construct & Transmit Ea 
        # from jam.network.node import node
        # await AssuranceDistribution().transmit(node, signr)
        # Clear for next time slot
        self.clear()

    def clear(self):
        self._collected = [False] * CORE_COUNT


assr_collector = AssuranceCollector()
