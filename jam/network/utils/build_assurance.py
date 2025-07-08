from sympy.physics.optics import rayleigh2waist
from tsrkit_types import structure, TypedVector, U32, U8
from jam.logging import get_logger

from jam import chain_config
from jam.types.work.shard import ShardIndex
from jam.types.protocol.core import ValidatorIndex
from jam.utils import constants
from jam.network.node import Node
from jam.work_package.stores.audits import AuditShardsDA
from jam.work_package.stores.reports import ReportsDA
from jam.work_package.stores.segments import SegmentShardsDA
from jam.types.protocol.crypto import Hash
from jam.network.protocols.ce_135 import GuaranteedWR
# from jam.types.block.extrinsics.assurances import AvailAssuranceNetwork
from jam.types.protocol.crypto import Ed25519Signature


def build_assurance() -> AvailAssuranceNetwork:


async def generate_assurance(self, report: GuaranteedWR, node: Node) -> AvailAssuranceNetwork :
    """ Here we use shard distributions """
    from jam.settings import settings


    slot = report.slot
    validator_index = ValidatorIndex(4)

    erasure_root = report.report.package_spec.erasure_root
    shard_index = ShardIndex((report.report.core_index * chain_config.erasure_coding_original_shards + validator_index) % constants.VALIDATOR_COUNT)

    from jam.network.protocols.ce_137 import ShardDistributionProtocol, CE137Data, Query
    CE137 = ShardDistributionProtocol()

    query = Query(shared_index=shard_index, erasure_root=erasure_root)
    data = CE137Data(len=U32(len(query.encode())), quesry=query) # here we get the shard

    shard = await CE137.transmit(node=node, data=data)

    header_hash = 0x5c743dbc514284b2ea57798787c5a155ef9d7ac1e9499ec65910a7a3d65897b7
    bitfield = TypedVector[U8]
    signature = Ed25519Signature(node.ed_key)


    # Save Shard
    if shard is not None:
        # Store Bundle Sharda
        print("shard received", shard)
        audits = settings.audit
        bs_da = AuditShardsDA(audits)
        bs_da.put(erasure_root, shard_index, shard[0])

        # Store Segments Shard
        d3l = settings.d3l
        ss_da = SegmentShardsDA(d3l)
        ss_da.put(erasure_root, shard_index, shard[1])

        # Distribute Assurance
        from jam.network.protocols.ce_141 import AssuranceDistribution, CE141Data
        CE141 = AssuranceDistribution()

        from jam.types.block.extrinsics.assurances import AvailAssurance

        assurance_per_node = AvailAssurance(
            anchor = header_hash,
            bitfield = bitfield,
            validator_index = validator_index,
            signature = Ed25519Signature(signature)
        )


        data = CE141Data(assurance_per_node)
        ack = await CE141.transmit(node=node, data=data)

        # Save Report
        rep_da = ReportsDA(d3l)
        wr_hash = Hash.blake2b(report.encode())
        rep_da.put(wr_hash, report)

        logger.info(f"📩 Assured work report : {wr_hash} with slot {slot}")

    else:
        bitfield.append(0)
        ass



    return assurance_per_node



