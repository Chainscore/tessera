import asyncio
from math import floor
from time import time

from tsrkit_types import Bytes, U16, Uint

from jam.execution.pvm.code import Code
from jam.types.protocol.crypto import Hash
from jam.types.work.item import WorkItem, ImportSpecs, ExtrinsicSpecs, ImportSpec
from jam.types.work.manifest import Extrinsics
from jam.utils.constants import EPOCH_LENGTH, GENESIS_TS
from jam.network.node import Node
from jam.logging import get_logger
from rockstore import RockStore
from jam.utils.dummy.dummy_package import create_dummy_package
from jam.network.protocols.ce_133 import WorkPackageSubmission, CE133Data
from jam.network.protocols.ce_133 import WorkPackageCore
from jam.types.protocol.core import CoreIndex, Gas, ServiceId, SegmentRoot

# Logger for WP Production
logger = get_logger("in_core")


async def wp_producer(node: Node, db: RockStore):
    """
    Continuously produces work packages and transmits them.
    A builder node produces a work package and share it with the guarantors.
    Args:
        node (Node): The network node for communications
        db (RockStore): The database to store the genesis timestamp
    """

    C133 = WorkPackageSubmission()

    wp_iter = 0

    logger.info(
        "Starting work package producer",
        node_name=node.name,
        is_builder=node.is_builder,
        genesis_timestamp=GENESIS_TS,
    )

    while True:
        has_40000 = any(peer.port == 40000 for peer in node.peer_conn)

        if not has_40000:
            logger.debug(
                "Network not initialized - skipping work package production",
                node_name=node.name,
                iteration=wp_iter,
            )
            await asyncio.sleep(6)
            continue

        # Get state from db
        from jam.state.state import state

        current_timeslot = (time() - GENESIS_TS) // 6

        # Get current timeslot
        ts_epoch_index = floor(current_timeslot % EPOCH_LENGTH)

        logger.debug(
            "Work package production cycle",
            node_name=node.name,
            iteration=wp_iter,
            current_timeslot=current_timeslot,
            epoch_index=ts_epoch_index,
            gamma_mode=state.gamma.s._choice_key,
        )

        if node.is_builder:
            wp = create_dummy_package()

            pc = bytes(
                [
                    0,
                    0,
                    22,
                    124,
                    121,
                    81,
                    25,
                    1,
                    7,
                    40,
                    2,
                    0,
                    149,
                    17,
                    255,
                    70,
                    1,
                    1,
                    100,
                    23,
                    51,
                    8,
                    1,
                    50,
                    0,
                    69,
                    147,
                    18,
                ]
            )
            c0_authorized_code = [
                0,
                0,
                21,
                124,
                121,
                81,
                9,
                6,
                40,
                2,
                0,
                149,
                17,
                255,
                70,
                1,
                1,
                100,
                23,
                51,
                8,
                1,
                50,
                0,
                165,
                73,
                9,
            ]
            code = Code(code=pc, read=b"", r_write=b"", z=0, s=100)
            bytecode = code.encode()
            service_code = Bytes(b"").encode() + bytecode
            code_hash = Hash.blake2b(service_code)

            wp.authorizer.code_hash = code_hash
            wp.authorization = Bytes(int(1).to_bytes(1))

            wi_pc = bytes(
                [
                    0,
                    0,
                    90,
                    51,
                    12,
                    149,
                    27,
                    0,
                    112,
                    254,
                    124,
                    117,
                    6,
                    40,
                    2,
                    200,
                    199,
                    3,
                    149,
                    51,
                    7,
                    200,
                    203,
                    4,
                    130,
                    57,
                    123,
                    73,
                    149,
                    204,
                    8,
                    172,
                    92,
                    240,
                    100,
                    194,
                    40,
                    2,
                    200,
                    203,
                    7,
                    51,
                    8,
                    20,
                    9,
                    255,
                    255,
                    255,
                    255,
                    255,
                    0,
                    0,
                    0,
                    51,
                    10,
                    5,
                    51,
                    11,
                    51,
                    12,
                    10,
                    18,
                    86,
                    23,
                    255,
                    9,
                    200,
                    114,
                    2,
                    40,
                    6,
                    51,
                    7,
                    40,
                    2,
                    149,
                    23,
                    0,
                    112,
                    254,
                    100,
                    40,
                    10,
                    19,
                    149,
                    23,
                    0,
                    112,
                    254,
                    51,
                    8,
                    50,
                    0,
                    133,
                    148,
                    164,
                    146,
                    74,
                    1,
                    164,
                    138,
                    84,
                    161,
                    66,
                    1,
                ]
            )
            #
            wi_code = Code(code=wi_pc, read=b"", r_write=b"", z=0, s=(1024 * 100))
            wi_bytecode = wi_code.encode()
            wi_service_code = Bytes(b"").encode() + wi_bytecode
            wi_code_hash = Hash.blake2b(wi_service_code)
            wi_service = ServiceId(1)
            # "3cf9b7c011a52ccd5b2513c68cde23"

            # import_spec1 = ImportSpec(
            #     tree_root=SegmentRoot(b"0x3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91"),
            #     index=U16(0))
            # import_spec2 = ImportSpec(
            #     tree_root=SegmentRoot(b"0x6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694"),
            #     index=U16(0))

            import_spec1 = ImportSpec(
                tree_root=SegmentRoot.fromhex(
                    "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91"
                ),
                index=U16(0),
            )
            import_spec2 = ImportSpec(
                tree_root=SegmentRoot.fromhex(
                    "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694"
                ),
                index=U16(0),
            )

            if wp_iter % 4 == 0:
                import_specs = []
            elif wp_iter % 4 == 1:
                import_specs = [import_spec1]
            elif wp_iter % 4 == 2:
                import_specs = [import_spec2]
            else:  # wp_iter % 4 == 3
                import_specs = [import_spec1, import_spec2]

            wi = WorkItem(
                service=wi_service,
                code_hash=wi_code_hash,
                payload=Bytes(b"bobaboba"),
                refine_gas_limit=Gas(1_000),
                accumulate_gas_limit=Gas(1_000),
                import_segments=ImportSpecs(import_specs),
                extrinsic=ExtrinsicSpecs([]),
                export_count=U16(1),
            )
            wp.items.append(wi)

            wc = WorkPackageCore(wp, CoreIndex(1))
            ext = Extrinsics([])

            package_len = Uint[32](len(wc.encode()))
            ext_len = Uint[32](len(ext.encode()))
            data = CE133Data(
                package_len=package_len,
                package_data=wc,
                extrinsics_len=ext_len,
                extrinsics=ext,
            )

            logger.info(
                "Producing work package",
                node_name=node.name,
                iteration=wp_iter,
                core_index=1,
                extrinsics_count=0,
                current_timeslot=current_timeslot,
            )

            # TODO: Implement package transmission

            responses = await C133.transmit(node, data)
            logger.debug(
                "Work package transmitted", node_name=node.name, iteration=wp_iter
            )

        else:
            logger.debug(
                "Node is not builder - skipping work package production",
                node_name=node.name,
                iteration=wp_iter,
            )

        # Sleep for remaining time of the timeslot
        await asyncio.sleep(6 - (time() - GENESIS_TS) % 6)
        wp_iter += 1
