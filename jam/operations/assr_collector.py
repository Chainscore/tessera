from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jam.utils.constants import CORE_COUNT
from tsrkit_types import Bytes
from typing import List 

class AssuranceCollector:
    _collected: List[bool]

    def __init__(self) -> None:
        self._collected = []

    def record_shard_assr(self, core_index: int):
        self._collected[core_index] = True 
    
    async def run(self, time_slot: int) -> bytes:
        # TODO: Check structure
        from jam.settings import settings
        signr = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private).sign(
            Bytes.from_bits(self._collected)
        )
        print("Operator for assr collector", time_slot, signr.hex())
    
    def clear(self):
        self._collected = [False] * CORE_COUNT


assr_collector = AssuranceCollector()
