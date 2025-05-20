import asyncio
from math import floor
from time import time

from jam.execution.pvm.code import Code
from jam.state.accounts import AccountMetadata
from jam.state.ghost import GhostState
from jam.state.state import State
from jam.types.base import Bytes, U16
from jam.types.protocol.crypto import Hash
from jam.types.state.delta import Ai, Ao, Timestamps, LookupTable
from jam.types.work.item import WorkItem, ImportSpecs, ExtrinsicSpecs, ImportSpec
from jam.types.work.manifest import Extrinsics, Extrinsic
from jam.utils.codec.primitives.bytes import BytesCodec
from jam.utils.constants import EPOCH_LENGTH
from jam.network.node import Node
from jam.config.logging import logger
from jam.storage.db.kv import KVStore
from tests.dummy.dummy_package import create_dummy_package
from jam.network.protocols.ce_133 import WorkPackageSubmission, CE133Data
from jam.network.protocols.ce_133 import WorkPackageCore
from jam.types.protocol.core import CoreIndex, Gas, Balance, BlobLength, ServiceId, SegmentRoot


async def wp_producer(node: Node, db: KVStore):
    """
    Continuously produces work packages and transmits them.
    A builder node produces a work package and share it with the guarantors.
    Args:
        node (Node): The network node for communications
        db (KVStore): The database to store the genesis timestamp
    """


    # Record genesis timestamp in seconds
    genesis_ts = time()
    C133 = WorkPackageSubmission()

    wp_iter = 0
    while True:
        print("time", genesis_ts, time())
        if not node.is_initialized:
            logger.info(f"🔄 ({node.name}) Network is not initialized, skipping packages production")
            await asyncio.sleep(6)
            genesis_ts = time()
            continue

        # Get state from db
        from jam.state.state import state

        current_timeslot = (time() - genesis_ts) // 6

        # Get current timeslot
        ts_epoch_index = floor(current_timeslot % EPOCH_LENGTH)

        logger.info(f"We're in epoch slot {ts_epoch_index} and {state.gamma.s.get_key()} mode")

        if node.is_builder:
            wp = create_dummy_package()

            pc = bytes(
                [0, 0, 22, 124, 121, 81, 25, 1, 7, 40, 2, 0, 149, 17, 255, 70, 1, 1, 100, 23, 51, 8, 1, 50, 0, 69, 147,
                 18])
            c0_authorized_code = [0, 0, 21, 124, 121, 81, 9, 6, 40, 2, 0, 149, 17, 255, 70, 1, 1, 100, 23, 51, 8, 1, 50,
                                  0, 165, 73, 9]
            code = Code(code=pc, read=b"", r_write=b"", z=0, s=100)
            bytecode = code.encode()
            service_code = BytesCodec().encode(value=b"") + bytecode
            code_hash = Hash.blake2b(service_code)

            state.delta[wp.auth_code_host] = AccountMetadata(code_hash=code_hash, balance=Balance(1_000_000),
                                                                  gas_limit=Gas(1_000), min_gas=Gas(1_000), num_i=Ai(0),
                                                                  num_o=Ao(0))
            state.delta[wp.auth_code_host].lookup[code_hash] = Bytes(service_code)
            state.delta[wp.auth_code_host].timestamps[
                LookupTable(hash=code_hash, length=BlobLength(len(service_code)))] = Timestamps([state.tau])
            wp.code_hash = code_hash
            wp.authorization = Bytes(int(1).to_bytes(1))

            wi_pc = bytes(
                [0, 0, 90, 51, 12, 149, 27, 0, 112, 254, 124, 117, 6, 40, 2, 200, 199, 3, 149, 51, 7, 200, 203, 4, 130,
                 57, 123, 73, 149, 204, 8, 172, 92, 240, 100, 194, 40, 2, 200, 203, 7, 51, 8, 20, 9, 255, 255, 255, 255,
                 255, 0, 0, 0, 51, 10, 5, 51, 11, 51, 12, 10, 18, 86, 23, 255, 9, 200, 114, 2, 40, 6, 51, 7, 40, 2, 149,
                 23, 0, 112, 254, 100, 40, 10, 19, 149, 23, 0, 112, 254, 51, 8, 50, 0, 133, 148, 164, 146, 74, 1, 164,
                 138, 84, 161, 66, 1]
            )

            wi_code = Code(code=wi_pc, read=b"", r_write=b"", z=0, s=(1024 * 100))
            wi_bytecode = wi_code.encode()
            wi_service_code = BytesCodec().encode(value=b"") + wi_bytecode
            wi_code_hash = Hash.blake2b(wi_service_code)
            wi_service = ServiceId(1)

            state.delta[wi_service] = AccountMetadata(code_hash=wi_code_hash, balance=Balance(1_000_000),
                                                      gas_limit=Gas(1_000), min_gas=Gas(1_000), num_i=Ai(0),
                                                      num_o=Ao(0))
            state.delta[wi_service].lookup[wi_code_hash] = Bytes(wi_service_code)
            state.delta[wi_service].timestamps[
                LookupTable(hash=wi_code_hash, length=BlobLength(len(wi_service_code)))] = Timestamps([state.tau])

            import_spec1 = ImportSpec(tree_root=SegmentRoot("0x3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91"), index=U16(0))
            import_spec2 = ImportSpec(tree_root=SegmentRoot("0x6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694"), index=U16(0))

            if current_timeslot % 4 == 0:
                import_specs = []
            elif current_timeslot % 4 == 1:
                import_specs = [import_spec1]
            elif current_timeslot % 4 == 2:
                import_specs = [import_spec2]
            else:  # current_timeslot % 4 == 3
                import_specs = [import_spec1, import_spec2]

            wi = WorkItem(
                service=wi_service,
                code_hash=wi_code_hash,
                payload=Bytes(b"bobaboba"),
                refine_gas_limit=Gas(1_000),
                accumulate_gas_limit=Gas(1_000),
                import_segments=ImportSpecs(import_specs),
                extrinsic=ExtrinsicSpecs([]),
                export_count=U16(1)
            )
            wp.items.append(wi)

            wc = WorkPackageCore(wp, CoreIndex(1))

            data = CE133Data(package_data=wc, extrinsics=Extrinsics([Extrinsic(b"hello")]))
            logger.info(f"⛏️ ({node.name}) Producing Work Package { wp}")
            # TODO: Implement package transmission

            C133.transmit(node, data)
        else:
            logger.info(f"⛏️ ({node.name}) skipping Node")


        # Sleep for remaining time of the timeslot
        await asyncio.sleep(6 - (time() - genesis_ts) % 6)
        wp_iter += 1