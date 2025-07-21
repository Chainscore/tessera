import pytest
import os

from jam.network.node import setup_node
from jam.settings import setup_setting
from tests.unit.wp.types import RefineVectors
import asyncio
import json
import logging
import os
import time

from asyncio import CancelledError
from dotenv import load_dotenv
from jam.operations.operator import operate
from jam.api.rpc.app import rpc
from jam.logging import setup_logging, logger
from jam.network.base.certificate import generate_san
from jam.utils.chainspec import chain_config
from jam.settings import setup_setting
from jam.consensus.grandpa.finality import Finality
from jam.network.peer import Peer
from jam.network.node import setup_node
from jam.operations.utils.state_update import update_state
from jam.state.state import setup_state
from jam.types.block import Block
from jam.utils.constants import GENESIS_TS, SLOT_PERIOD, EPOCH_LENGTH

TIMESLOT = 0


vectors: RefineVectors = RefineVectors.from_json(
    [
        {
            "work_package": {
                "authorization": "01",
                "auth_code_host": 42,
                "authorizer": {
                    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
                    "params": "d914a1f4c711d703a16f",
                },
                "context": {
                    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor_slot": 0,
                    "prerequisites": [],
                },
                "items": [
                    {
                        "service": 1,
                        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
                        "payload": "626f6261626f6261",
                        "refine_gas_limit": 1000,
                        "accumulate_gas_limit": 1000,
                        "import_segments": [],
                        "extrinsic": [],
                        "export_count": 1,
                    }
                ],
            },
            "core_index": 1,
            "extrinsics": [],
            "work_rep": {
                "package_spec": {
                    "hash": "3af24a613bc9feea59dcd6c1e3ab44b199794e8507e2ef886eca276ea2f46f0d",
                    "length": 253,
                    "erasure_root": "6a0e4a8c7c232b28a3983ccc4260d0d16c81fc1550eea136dedd51c9a854a300",
                    "exports_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
                    "exports_count": 1,
                },
                "context": {
                    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor_slot": 0,
                    "prerequisites": [],
                },
                "core_index": 1,
                "authorizer_hash": "459cd4362e25bdcf6d6260b9cfd206b11d89a8b006d5cd32e029777385a03192",
                "auth_output": "01",
                "segment_root_lookup": {},
                "results": [
                    {
                        "service_id": 1,
                        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
                        "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
                        "accumulate_gas": 1000,
                        "result": {"ok": ""},
                        "refine_load": {
                            "gas_used": 49,
                            "imports": 0,
                            "extrinsic_count": 0,
                            "extrinsic_size": 0,
                            "exports": 1,
                        },
                    }
                ],
                "auth_gas_used": 7,
            },
            "rep_hash": "dc71f2c6f1d2ce6f3cce7362b143aa1939de5d59cc3c042e26e9d1af4f17fe76",
        },
        {
            "work_package": {
                "authorization": "01",
                "auth_code_host": 42,
                "authorizer": {
                    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
                    "params": "34401c7359774f241912",
                },
                "context": {
                    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor_slot": 0,
                    "prerequisites": [],
                },
                "items": [
                    {
                        "service": 1,
                        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
                        "payload": "626f6261626f6261",
                        "refine_gas_limit": 1000,
                        "accumulate_gas_limit": 1000,
                        "import_segments": [
                            {
                                "tree_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
                                "index": 0,
                            }
                        ],
                        "extrinsic": [],
                        "export_count": 1,
                    }
                ],
            },
            "core_index": 1,
            "extrinsics": [],
            "work_rep": {
                "package_spec": {
                    "hash": "38f60390b2b74203d01b6c3d18700c30963aeddcbc0ce08573ae74f37f17224a",
                    "length": 4425,
                    "erasure_root": "27272da2c88f8106289bfbf1e0330831362e7cd0a200ecbd5cff160048ebcde3",
                    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
                    "exports_count": 1,
                },
                "context": {
                    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor_slot": 0,
                    "prerequisites": [],
                },
                "core_index": 1,
                "authorizer_hash": "587d37dafe7e73d6074d03a8eb80d14b8af552599e4437c6c68aa1f30bdaf0b6",
                "auth_output": "01",
                "segment_root_lookup": {},
                "results": [
                    {
                        "service_id": 1,
                        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
                        "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
                        "accumulate_gas": 1000,
                        "result": {"ok": ""},
                        "refine_load": {
                            "gas_used": 49,
                            "imports": 1,
                            "extrinsic_count": 0,
                            "extrinsic_size": 0,
                            "exports": 1,
                        },
                    }
                ],
                "auth_gas_used": 7,
            },
            "rep_hash": "7688fa8846a5596ebb7a8d715327e0dce7058e1c65e9298bae897d23733755ba",
        },
        {
            "work_package": {
                "authorization": "01",
                "auth_code_host": 42,
                "authorizer": {
                    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
                    "params": "bcf3588ab585a854fe37",
                },
                "context": {
                    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor_slot": 0,
                    "prerequisites": [],
                },
                "items": [
                    {
                        "service": 1,
                        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
                        "payload": "626f6261626f6261",
                        "refine_gas_limit": 1000,
                        "accumulate_gas_limit": 1000,
                        "import_segments": [
                            {
                                "tree_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
                                "index": 0,
                            }
                        ],
                        "extrinsic": [],
                        "export_count": 1,
                    }
                ],
            },
            "core_index": 1,
            "extrinsics": [],
            "work_rep": {
                "package_spec": {
                    "hash": "bfaacb611675602f6857708283e327c3263ea951f30d07d82e3b88e36a6073e4",
                    "length": 4425,
                    "erasure_root": "b8880fe309668f83d395131a6b856ce2b815a562272f0de764749bd3d0d492c7",
                    "exports_root": "2e2ea8b591ef3684aabc518001bf43a3ddfe6be2ada603d3501261b6b5dac2c8",
                    "exports_count": 1,
                },
                "context": {
                    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor_slot": 0,
                    "prerequisites": [],
                },
                "core_index": 1,
                "authorizer_hash": "ff22ab2fabe104fe12e79bdf463a003c8d4d6c62c786a641699cbcdbd3f2c5be",
                "auth_output": "01",
                "segment_root_lookup": {},
                "results": [
                    {
                        "service_id": 1,
                        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
                        "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
                        "accumulate_gas": 1000,
                        "result": {"ok": ""},
                        "refine_load": {
                            "gas_used": 49,
                            "imports": 1,
                            "extrinsic_count": 0,
                            "extrinsic_size": 0,
                            "exports": 1,
                        },
                    }
                ],
                "auth_gas_used": 7,
            },
            "rep_hash": "a164ca339cc8db81b843d3d19c96ceb7ef80cb377a22f3bacda6b880a91dc26d",
        },
        {
            "work_package": {
                "authorization": "01",
                "auth_code_host": 42,
                "authorizer": {
                    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
                    "params": "7c527627ba6fac003b71",
                },
                "context": {
                    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor_slot": 0,
                    "prerequisites": [],
                },
                "items": [
                    {
                        "service": 1,
                        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
                        "payload": "626f6261626f6261",
                        "refine_gas_limit": 1000,
                        "accumulate_gas_limit": 1000,
                        "import_segments": [
                            {
                                "tree_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
                                "index": 0,
                            },
                            {
                                "tree_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
                                "index": 0,
                            },
                        ],
                        "extrinsic": [],
                        "export_count": 1,
                    }
                ],
            },
            "core_index": 1,
            "extrinsics": [],
            "work_rep": {
                "package_spec": {
                    "hash": "74a94754a42b67ae9e311fb1025f4bd7829be9711c97aef2063b47b7e19c0b04",
                    "length": 8597,
                    "erasure_root": "12c4aaf66b033b8064142e35c2398782fe50c6cbfc6588a4d59f2c3e51f449c7",
                    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
                    "exports_count": 1,
                },
                "context": {
                    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor_slot": 0,
                    "prerequisites": [],
                },
                "core_index": 1,
                "authorizer_hash": "e84caad83e96d576aae85146afb2e30e59429ad8122cbe6307b5aa0846f38e84",
                "auth_output": "01",
                "segment_root_lookup": {},
                "results": [
                    {
                        "service_id": 1,
                        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
                        "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
                        "accumulate_gas": 1000,
                        "result": {"ok": ""},
                        "refine_load": {
                            "gas_used": 49,
                            "imports": 2,
                            "extrinsic_count": 0,
                            "extrinsic_size": 0,
                            "exports": 1,
                        },
                    }
                ],
                "auth_gas_used": 7,
            },
            "rep_hash": "dac97a8208e87abc357d958984d017a8ce43b29caa4bb49e800eaa5bafa1f091",
        },
        {
            "work_package": {
                "authorization": "01",
                "auth_code_host": 42,
                "authorizer": {
                    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
                    "params": "385e673167ab28c7aac5",
                },
                "context": {
                    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor_slot": 0,
                    "prerequisites": [],
                },
                "items": [
                    {
                        "service": 1,
                        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
                        "payload": "626f6261626f6261",
                        "refine_gas_limit": 1000,
                        "accumulate_gas_limit": 1000,
                        "import_segments": [],
                        "extrinsic": [],
                        "export_count": 1,
                    }
                ],
            },
            "core_index": 1,
            "extrinsics": [],
            "work_rep": {
                "package_spec": {
                    "hash": "bd270fed16ed99478aa2665d2c70c62016a34fc6c97217cf900bfcbee3b78bfb",
                    "length": 253,
                    "erasure_root": "e4e1aa59f7bf14447746d8b6f5371e236a226cab4ea8c1ffeffc1c588df30ff7",
                    "exports_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
                    "exports_count": 1,
                },
                "context": {
                    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lookup_anchor_slot": 0,
                    "prerequisites": [],
                },
                "core_index": 1,
                "authorizer_hash": "ee74022d4cc61e75e595432eeed50ce258d8d7411ab31bd304d2f2d07b36ed03",
                "auth_output": "01",
                "segment_root_lookup": {},
                "results": [
                    {
                        "service_id": 1,
                        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
                        "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
                        "accumulate_gas": 1000,
                        "result": {"ok": ""},
                        "refine_load": {
                            "gas_used": 49,
                            "imports": 0,
                            "extrinsic_count": 0,
                            "extrinsic_size": 0,
                            "exports": 1,
                        },
                    }
                ],
                "auth_gas_used": 7,
            },
            "rep_hash": "b0dc4df40d95f1c43ac4bb734b3eb3b0e813d3ca068baa74c3246d83507be941",
        },
    ]
)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_refinement():
    # ---------- SETUP LOGGING ----------
    genesis_ts = GENESIS_TS  # Actual Genesis time for JAM Common Era
    init_ts = int((time.time() - genesis_ts) // SLOT_PERIOD)
    init_ep = int(init_ts // EPOCH_LENGTH)

    global TIMESLOT
    TIMESLOT = init_ts

    # ---------- LOAD ENVIRONMENT ----------
    load_dotenv("../../../.env")
    load_dotenv("../../../envs/40000.env", override=True)

    name = "ALICE"
    port = 40000
    seed = 0
    host = "127.0.0.1"
    logger.info("SET HOST", host=host)

    # ---------- SETUP LOGGING ----------
    environment = os.environ.get("ENVIRONMENT", "development")
    log_level = os.environ.get("LOG_LEVEL", None)

    setup_logging(
        theme="polkadot",
        node_name=name,
        environment=environment,
        min_level=getattr(logging, log_level.upper()) if log_level else None,
    )

    # ---------- SETUP SETTINGS ----------
    settings = setup_setting(name="TESTER", port=40000, seed=int(0), data_path="data/")

    main_db = settings.main_db

    logger.info(
        "Starting JAM node",
        name=name,
        port=port,
        ts=init_ts,
        epoch=init_ep,
        spec=chain_config.name,
    )

    try:
        genesis_path = ""
        # -------------- SETUP STATE -------------
        # Set genesis state
        dev_spec = json.load(open(genesis_path))
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
        state = setup_state(settings.state_db, genesis_path)
        state.store.disable_cache()
        update_state(state)

        # ----------- SETUP NETWORKING ------------
        peers = [Peer(data=val) for val in state.kappa if val.metadata.port != port]

        tsr_node = setup_node(
            name, int(port), peers, host=str(host), is_bd=False, is_val=True
        )

        # ------------ SET GENESIS BLOCK ------------
        block = Block.decode(bytes.fromhex(dev_spec["genesis_header"]))
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)
        Finality.finalise(header_hash, main_db)

        from jam.work_package.processor import Processor

        processor = Processor(tsr_node)

        for i, v in enumerate(vectors):
            wr, wr_hash = processor.process(v.work_package, v.core_index, v.extrinsics)

            try:
                assert wr == v.work_rep
                assert wr_hash == v.rep_hash
            except Exception as e:
                print("ERROR", e, "for index", i)
    except Exception as e:
        logger.error("ERROR OCCURRED", err=e)

    # node = setup_node("127.0.0.1", 20001, )
