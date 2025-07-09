from jam.network.protocols.ce_141 import Assurance
import asyncio
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jam.logging import get_logger
from jam.network.protocols.ce_141 import AssuranceDistribution
from jam.types import Hash
from jam.types.block.extrinsics.assurances import AvailBitField
from jam.types.protocol.crypto import Ed25519Signature, HeaderHash
from jam.utils.constants import CORE_COUNT
from tsrkit_types import Bytes, U32
from typing import List



logger = get_logger("nodeops")

class AssuranceCollector:
    _collected: List[bool]

    def __init__(self) -> None:
        self._collected = [False] * CORE_COUNT


    def record_shard_assr(self, core_index: int):
        self._collected[core_index] = True 
        logger.debug("Recorded shard for core", core_index=core_index)
    
    async def run(self, time_slot: int):
        from jam.settings import settings
        from jam.network.node import node
        pref = Bytes('jam_available', 'utf-8')



        from jam.network.protocols.ce_141 import CE141Data,AssuranceDistribution
        from jam.consensus.grandpa.finality import Finality

        try:
            latest_block = Finality.load_latest(kv=settings.main_db)
            header_hash = latest_block.header.hash()
            # TODO: Construct & Transmit Ea
            sign_data = header_hash.encode() + Bytes.from_bits(self._collected)

            signr = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private).sign(
                pref + Hash.blake2b(sign_data)
            )
            CE141 = AssuranceDistribution()
            assurance = Assurance(
                anchor_hash=HeaderHash(header_hash),
                bitfield=AvailBitField(self._collected),
                ed25519_signature=Ed25519Signature(signr)
            )
            data = CE141Data(
                assurance=assurance,
                len=U32(len(assurance.encode()))
            )
            asyncio.create_task(CE141.transmit(node=node, data=data))
        except Exception as e:
            logger.error("Failed to record assurance", time_slot=time_slot)
        self.clear()

    def clear(self):
        self._collected = [False] * CORE_COUNT


assr_collector = AssuranceCollector()
