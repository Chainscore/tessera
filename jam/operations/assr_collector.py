from typing import cast, TYPE_CHECKING

from jam.network.protocols.ce_141 import Assurance

if TYPE_CHECKING:
    from jam.network.node import Node

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
<<<<<<< HEAD
from jam.logging import get_logger
from jam.network.protocols.ce_141 import AssuranceDistribution
=======
>>>>>>> 1431083aa886ddb4580679deaeb09d8d90174ad1
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
    
    async def run(self, time_slot: int, node: Node):
        from jam.settings import settings
        signr = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private).sign(
            Bytes.from_bits(self._collected)
        )
        from jam.network.protocols.ce_141 import CE141Data,AssuranceDistribution
        from jam.consensus.grandpa.finality import Finality

        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()

        # TODO: Construct & Transmit Ea
        CE141 = AssuranceDistribution()

        assurance = Assurance(
            header_hash=header_hash,
            bitfield=self._collected,
            ed25519_signature=signr
        )

        data = CE141Data(
            assurance=assurance,
            len=U32(len(assurance.encode()))
        )

        acks =  CE141.transmit(node=node, data=data)

        self.clear()

    def clear(self):
        self._collected = [False] * CORE_COUNT


assr_collector = AssuranceCollector()
