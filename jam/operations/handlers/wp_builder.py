import os
from tsrkit_types import Bytes, U16, Uint

from jam.execution.pvm.code import Code
from jam.types import WorkPackage
from jam.types.protocol.crypto import Hash
from jam.types.work.item import WorkItem, ImportSpecs, ExtrinsicSpecs, ImportSpec
from jam.types.work.manifest import Extrinsics, Extrinsic
from jam.utils.constants import EPOCH_LENGTH, SLOT_PERIOD, GENESIS_TS
from jam.logging import get_logger
from jam.utils.dummy.dummy_package import create_dummy_package
from jam.network.protocols.ce_133 import WorkPackageSubmission, CE133Data
from jam.network.protocols.ce_133 import WorkPackageCore
from jam.types.protocol.core import CoreIndex, Gas, ServiceId, SegmentRoot

# Logger for WP Production
logger = get_logger("builder")


class WPBuilder:
    """
    WP Engine: Continuously produces work packages and transmits them.
    Work Package is shared $SLOT_PERIOD seconds apart.
    A builder node produces a work package and share it with the guarantors.

    Args:
        node (Node): The network node for communications
        settings (Settings): Settings related to node
    """

    @classmethod
    async def run(cls, time_slot: int):
        """
        Starts the WP producer engine in asyncio loop.
        Assumes that the node is initialized and the latest synchronized state is stored in the db.
        """
        from jam.network.start import node

        CE133 = WorkPackageSubmission()

        wp_iter = time_slot % 4

        curr_ts = time_slot
        curr_ep = int(curr_ts // EPOCH_LENGTH)

        # TODO: Remove hard-coded transmission. Use desired guarantors' connections.
        if not node:
            logger.debug(
                "Network not initialized - skipping work package production",
                # node_name=node.name,
                iteration=wp_iter,
            )
            return

        # Get state from db
        from jam.state.state import state

        logger.debug(
            "Work package production cycle",
            # node_name=node.name,
            iteration=wp_iter,
            curr_timeslot=curr_ts,
            curr_epoch=curr_ep,
            gamma_mode=state.gamma.s._choice_key,
        )

        wp = cls._build_package(wp_iter)

        wc = WorkPackageCore(wp, CoreIndex(1))
        ext = Extrinsics([Extrinsic(b"") for i in range(len(wp.items))])


        package_len = Uint[32](len(wc.encode()))
        ext_len = Uint[32](len(ext.encode()))
        data = CE133Data(
            package_len=package_len, package_data=wc, extrinsics_len=ext_len, extrinsics=ext
        )

        logger.info(
            "Producing work package",
            iteration=wp_iter,
            core_index=1,
            extrinsics_count=0,
            curr_timeslot=curr_ts,
        )

        responses = await CE133.transmit(data)
        logger.debug("Work package transmitted",
                     # node_name=node.name,
                     iteration=wp_iter)

    @staticmethod
    def _build_package(wp_iter: int) -> WorkPackage:
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

        wi_code = Code(code=wi_pc, read=b"", r_write=b"", z=0, s=(1024 * 100))
        wi_bytecode = wi_code.encode()
        wi_service_code = Bytes(b"").encode() + wi_bytecode
        wi_code_hash = Hash.blake2b(wi_service_code)
        wi_service = ServiceId(1)

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

        import_specs = []

        wi = WorkItem(
            service=wi_service,
            code_hash=wi_code_hash,
            payload=Bytes(os.urandom(256)),
            refine_gas_limit=Gas(1_000),
            accumulate_gas_limit=Gas(1_000),
            import_segments=ImportSpecs(import_specs),
            extrinsic=ExtrinsicSpecs([]),
            export_count=U16(1),
        )
        wp.items.append(wi)

        return wp
