import os
import asyncio
import pytest
import shutil

from multiprocessing import Process

from tsrkit_types import TypedVector, Dictionary
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import Uint, U16, U32, U64

from jam.models import (
    WorkReport,
    WorkPackage,
    Authorizer,
    RefineContext,
    ImportSpec,
    ExtrinsicSpec,
    WorkItem,
    OpaqueHash,
    WorkPackageSpec,
    WorkDigest,
    WorkExecResult,
    WorkReportHash,
    HeaderHash,
    StateRoot,
    BeefyRoot,
    WorkPackageHash,
    ErasureRoot,
    ExportsRoot,
)
from jam.models.work import RefineLoad

from jam.models.work.manifest import Extrinsics, Extrinsic
from jam.log_setup import node_logger as logger
from jam.network.protocols.ce_133 import WorkPackageSubmission, CE133Data
from jam.network.protocols.ce_133 import WorkPackageCore
from jam.models.protocol.core import CoreIndex
from jam.storage.da.reports import ReportsDA
from tests.integration.jamnp.utils.run_node import run_node_process

# CLIENTS = [
#     {"port": 40000, "role": "VALIDATOR", "theme": "matrix", "genesis": True},
#     # {
#     #     "port": 40001,
#     #     "role": "VALIDATOR",
#     #     "theme": "default",
#     #     "genesis": True
#     # },
#     # {
#     #     "port": 40006,
#     #     "role": "BUILDER",
#     #     "theme": "polkadot",
#     #     "genesis": True
#     # },
# ]

CLIENTS = [
    {"port": 40000, "role": "VALIDATOR", "theme": "matrix", "genesis": True},
    {
        "port": 40001,
        "role": "VALIDATOR",
        "theme": "default",
        "genesis": True
    },
    {
        "port": 40002,
        "role": "VALIDATOR",
        "theme": "default",
        "genesis": True
    },
    {
        "port": 40003,
        "role": "VALIDATOR",
        "theme": "default",
        "genesis": True
    },
    {
        "port": 40004,
        "role": "VALIDATOR",
        "theme": "default",
        "genesis": True
    },
    {
        "port": 40005,
        "role": "VALIDATOR",
        "theme": "default",
        "genesis": True
    },
    # {
    #     "port": 40006,
    #     "role": "BUILDER",
    #     "theme": "polkadot",
    #     "genesis": True
    # },
]


wp = WorkPackage(
    authorization=Bytes(b"\x01"),
    auth_code_host=U32(42),
    authorizer=Authorizer(
        code_hash=OpaqueHash(
            b'\x10S&j\x87\x96\xf3\xfb\xb2\x93b3\xf7\xb0"\x18iK\x04\xe8`J\xc3\xc8\x89.AT)\xf0\xa1-'
        ),
        params=Bytes(b"\x9a\xb5\xae\xec\xe7y0\xccP\x17"),
    ),
    context=RefineContext(
        anchor=HeaderHash(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        state_root=StateRoot(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        beefy_root=BeefyRoot(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        lookup_anchor=HeaderHash(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        lookup_anchor_slot=U32(0),
        prerequisites=TypedVector[OpaqueHash]([]),
    ),
    items=TypedVector[WorkItem](
        [
            WorkItem(
                service=U32(1),
                code_hash=OpaqueHash(
                    b"s\x8b\x9a\xff:\xcb\xcc\xabvnE\xcaN\xe1\x1d\x1d\xb9c\xca\xd1|\x9b\x931\xb2\xdaK\x10\xba@\xa8\x94"
                ),
                payload=Bytes(b"bobaboba"),
                refine_gas_limit=U64(1000),
                accumulate_gas_limit=U64(1000),
                import_segments=TypedVector[ImportSpec]([]),
                extrinsic=TypedVector[ExtrinsicSpec]([]),
                export_count=U16(1),
            )
        ]
    ),
)
wr = WorkReport(
    package_spec=WorkPackageSpec(
        hash=WorkPackageHash(
            b"}\xc8\xf4d\xb3\x1fH\xa0\xe4\x9c\x1f\x96\x86\xfd\xcb\x13\xd8\xde\xee%c\xee!d\xac\x88\xefg\x8b\xdd\xf7G"
        ),
        length=U32(253),
        erasure_root=ErasureRoot(
            b"4k;3U19\xea0\xf9YC\xe86\x0c\xa2\xd4p\xefmf\xfb\xa9\x03\xcb`\xefl\xd4M\xaf\x02"
        ),
        exports_root=ExportsRoot(
            b"<\xf9\xb7\xc0\x11\xa5,\xcd[%\x13\xc6\x8c\xde#\xeb\xa2\x07Hst\xb0tt-\xa4\x13\xd9\x05&;\x91"
        ),
        exports_count=U16(1),
    ),
    context=RefineContext(
        anchor=HeaderHash(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        state_root=StateRoot(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        beefy_root=BeefyRoot(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        lookup_anchor=HeaderHash(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        lookup_anchor_slot=U32(0),
        prerequisites=TypedVector[OpaqueHash]([]),
    ),
    core_index=Uint(1),
    authorizer_hash=b"\x9e\xcc\x01*<\xc8\xbbzG}\xef(\xac\xfd\xb6\xe5\xb0Y\xd7\xccU9y\x98\x95,\xefY\xa9\x1a\x18\x86",
    auth_output=b"\x01",
    segment_root_lookup=Dictionary({}),
    digests=TypedVector[WorkDigest](
        [
            WorkDigest(
                service_id=U32(1),
                code_hash=b"s\x8b\x9a\xff:\xcb\xcc\xabvnE\xcaN\xe1\x1d\x1d\xb9c\xca\xd1|\x9b\x931\xb2\xdaK\x10\xba@\xa8\x94",
                payload_hash=b"\xad\x83\xe1\x97-\xd0\xa6\x04\xeb\xe9\x85|\xad\xf9\x0f\x9a\x96\xc3,\xf4|{\x82\xc8\x04\xfb\xe8=\x0e\xaa\xf0\xaf",
                accumulate_gas=U64(1000),
                result=WorkExecResult(b""),
                refine_load=RefineLoad(
                    gas_used=Uint(49),
                    imports=Uint(0),
                    extrinsic_count=Uint(0),
                    extrinsic_size=Uint(0),
                    exports=Uint(1),
                ),
            )
        ]
    ),
    auth_gas_used=Uint(7),
)
wr_hash = WorkReportHash(
    b"\x18is\xa2\xd8\x8e\x15\xbd5H\xc6\xd3\xe3\xed\x87\xd6?s\xae\x1aT\xe8\x04\x9eQ\xea\xdc\xcd\x9e\x88\xfcs"
)
wc = WorkPackageCore(wp, CoreIndex(1))
ext = Extrinsics([Extrinsic(b"") for i in range(len(wp.items))])
from tests.unit.incore.types import RefineVectors

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


async def node_task():
    """Define Node tasks"""

    from jam.network.start import node
    # Wait for node to initialize
    await asyncio.sleep(5)
    print("NODE STARTED")

    if node.port == 40005:
        from jam.incore.processor import Processor

        processor = Processor()

        for i, v in enumerate(vectors):
            wr, wr_hash = await processor.process(v.work_package, v.core_index, v.extrinsics)

            print('wr', wr)
            print('wr_hash', wr_hash)

            try:
                assert wr == v.work_rep
                assert wr_hash == v.rep_hash
            except Exception as e:
                print("ERROR", e, "for index", i)
        # protocol = WorkPackageSubmission()
        #
        #
        # package_len = Uint[32](len(wc.encode()))
        # ext_len = Uint[32](len(ext.encode()))
        # data = CE133Data(package_len=package_len, package_data=wc, extrinsics_len=ext_len, extrinsics=ext)
        #
        # responses = await protocol.transmit(node, data)
        #
        # # expected_message = Bool(True)
        #
        # for response in responses:
        #     # print("resp", response)
        #     assert response.unwrap()._value == True
        #     print("BUILDER ASSERTION SUCCESS")

    # else:
    #     # Wait for refinement to happen
    #     await asyncio.sleep(20)
    #     from jam.settings import settings
    #
    #     # Check if report exists in db or not
    #     try:
    #         db = settings.d3l
    #         da = ReportsDA(db)
    #
    #         rep = da.get(wr_hash)
    #         assert rep == wr
    #         print("WR ASSERTION SUCCESS")
    #
    #     except Exception as e:
    #         raise AssertionError("Report not found on Guarantor")


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_connection():
    print("START OF TEST")

    processes = []

    for client in CLIENTS:
        env_path = f"envs/{client['port']}.env"
        is_validator = client["role"] == "VALIDATOR"
        is_builder = client["role"] == "BUILDER"

        dir_path = f"/data/{client['port']}"

        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"REMOVED DIR: {dir_path}")

        p = Process(
            target=run_node_process,
            args=(
                "",
                env_path,
                client["genesis"],
                client["theme"],
                is_builder,
                is_validator,
                node_task,
            ),
        )
        processes.append(p)

    print("STARTING PROCESSES...")
    for p in processes:
        p.start()

    print("ALL PROCESSES STARTED")

    # KEEP TEST ALIVE FOR SOME TIME
    await asyncio.sleep(2000)

    print("TERMINATING PROCESSES")
    for p in processes:
        p.terminate()
    for p in processes:
        p.join()

    print("END OF TEST")
