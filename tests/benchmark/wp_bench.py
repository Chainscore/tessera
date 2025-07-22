import time
import os

from jam.state.state import setup_state
from jam.types import IPAddress, ValidatorData, BlsPublic, ValidatorMetadata
from jam.utils.dummy.dummy_package import create_dummy_package
from jam.execution.pvm.code import Code
from tsrkit_types import Bytes, TypedVector
from jam.types.protocol.crypto import Hash
from jam.types.protocol.core import CoreIndex, Gas, ServiceId, SegmentRoot
from jam.types.work.item import WorkItem, ImportSpecs, ExtrinsicSpecs, ImportSpec
from jam.network.node import Node
from jam.incore.processor import Processor
from tsrkit_types.integers import U16, U8, Uint
from jam.network.peer import Peer
from jam.settings import settings, setup_setting
from jam.utils.benchmark import benchmark
from dotenv import load_dotenv


def wp_bench():
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
        tree_root=SegmentRoot(
            b"0x3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91"
        ),
        index=U16(0),
    )
    import_spec2 = ImportSpec(
        tree_root=SegmentRoot(
            b"0x6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694"
        ),
        index=U16(0),
    )

    # if current_timeslot % 4 == 0:
    #     import_specs = []
    # elif current_timeslot % 4 == 1:
    #     import_specs = [import_spec1]
    # elif current_timeslot % 4 == 2:
    #     import_specs = [import_spec2]
    # else:  # current_timeslot % 4 == 3
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

    load_dotenv(".env")
    load_dotenv("40000.env")
    setup_setting(name="name", port=int(3000), seed=50, data_path="data/")
    state = setup_state(settings.state_db, "/dev-spec.json")
    state.store.disable_cache()
    peers = [
        Peer(id=bytes.decode(val.metadata.name, "utf-8"), data=val)
        for val in state.kappa
        if val.metadata.port != 3000
    ]
    node = Node(
        node_name="name",
        host="127.0.0.1",
        port=int(3000),
        peers=peers,
        validator_data=ValidatorData(
            keys.bandersnatch_public,
            keys.ed25519_public,
            BlsPublic(bytes(144)),
            ValidatorMetadata(
                name=Bytes[10](bytes(10)),
                protocol=Uint[16](2**16 - 1),
                host=IPAddress([U8(127), U8(0), U8(0), U8(1)]),
                port=U16(3000),
            ),
        ),
        is_builder=False,
        is_validator=True,
    )

    start = time.perf_counter()

    process = Processor(node)
    with benchmark("work package processing"):
        process.process(package=wp, core=CoreIndex(1), extrinsics=[Bytes(b"2172636nds")])

    end = time.perf_counter()
    print(f"Execution time for wp_process function: {end - start:.6f} seconds")


wp_bench()
