from dataclasses import dataclass
import json
import os
from typing import List

from jam.preimages.errors import PreimageErrorEnum
from jam.state.components.delta import Timestamps
from jam.types import OpaqueHash, decodable_choice, Null, Choice, Nullable
from jam.types.base.integers.fixed import U32
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.types.extrinsics.preimages import PreimagesExtrinsic
from jam.types.base.sequences.vector import decodable_vector, Vector
from jam.types.base import Bytes
from jam.types.base.sequences.bytes import ByteArray32
from jam.state.components.delta import LookupTable

@decodable_dataclass
@dataclass
class Input(Codable, JsonSerde):
    slot: U32
    preimages: PreimagesExtrinsic


@decodable_dataclass
@dataclass
class Preimage(Codable, JsonSerde):
    hash: OpaqueHash
    blob: Bytes

@decodable_vector(Preimage)
class Preimages(Vector): ...

@decodable_vector(U32, 3)
class LookupMetaValue(Vector): ...

@decodable_dataclass
@dataclass
class LookupMeta(Codable, JsonSerde):
    key: LookupTable
    value: Timestamps

@decodable_vector(LookupMeta)
class LookupMetas(Vector): ...

@decodable_dataclass
@dataclass
class AccountData(Codable, JsonSerde):
    preimages: Preimages
    lookup_meta: LookupMetas

@decodable_dataclass
@dataclass
class Account(Codable, JsonSerde):
    id: U32
    data: AccountData

@decodable_vector(Account)
class Accounts(Vector): ...

@decodable_dataclass
@dataclass
class PreState(Codable, JsonSerde):
    accounts: Accounts

PostState = PreState

@decodable_choice
class Output(Choice):
    ok: Nullable
    err: PreimageErrorEnum

@decodable_dataclass
@dataclass
class Testcase(Codable, JsonSerde):
    input: Input
    pre_state: PreState
    post_state: PostState
    output: Output

def get_testcases_starting_with(prefix: str = "", limit: int = 10) -> List[Testcase]:
    data_dir = "tests/unit/preimages/data"
    result = []
    for index, file in enumerate(os.listdir(data_dir)):
        if len(result) >= limit:
            continue
        elif not file.startswith(prefix):
            continue
        elif file.endswith(".bin"):
            continue
        else:
            with open(os.path.join(data_dir, file), "r") as f:
                data = json.loads(f.read())
             
                try:
                    tc = Testcase.from_json(data)
                    print(f"Decoded {file}")
                    result.append(tc)
                except Exception as e:
                    print(f"❌ Failed to decode {file}: {e}")
                    continue
    return result
