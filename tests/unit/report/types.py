from dataclasses import dataclass
from jam.state.components.alpha import Alpha
from jam.state.components.beta import Beta
from jam.state.components.eta import Eta
from jam.state.components.psi import Psi, PsiO
from jam.types import decodable_vector, Array, Vector, U64
from jam.types.extrinsics import GuaranteesExtrinsic
from jam.types.work.refine_context import OpaqueHashes
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.state.components.rho import Rho, WorkReportState
from jam.types.base.integers.fixed import U32,I64
from jam.utils.constants import CORE_COUNT
from jam.state.components.kappa import Kappa
from jam.state.components.lambda_ import Lambda_
from tests.unit.recent_history.types import BetaInput
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import Balance,Gas
import json
import os
from typing import List
from jam.types.protocol.core import TimeSlot


@decodable_dataclass
@dataclass
class Input(Codable, JsonSerde):
    guarantees: GuaranteesExtrinsic
    slot : TimeSlot


@decodable_dataclass
@dataclass
class InputService(Codable,JsonSerde):
    code_hash: OpaqueHash
    balance:Balance
    min_item_gas: Gas
    min_memo_gas: Gas
    bytes: U64
    items: I64




@decodable_dataclass
@dataclass
class InputServices(Codable, JsonSerde):
    service:InputService

@decodable_dataclass
@dataclass
class InputAccData(Codable, JsonSerde):
    id: U64
    data: InputServices



@decodable_vector(InputAccData)
class InputAccount(Vector):
    ...


@decodable_dataclass
@dataclass
class PreState(Codable, JsonSerde):
    avail_assignments: Rho
    curr_validators: Kappa
    prev_validators: Lambda_
    entropy: Eta
    offenders: PsiO
    recent_blocks: BetaInput
    auth_pools: Alpha
    accounts: InputAccount


PostState = PreState

@decodable_dataclass
@dataclass
class Testcase(Codable, JsonSerde):
    input: Input
    pre_state: PreState
    output: dict
    post_state: PostState



def get_testcases_starting_with(prefix: str = "reports_with_dependencies-1.json", limit: int = 1) -> List[Testcase]:
    data_dir = "/home/dikshant441/Desktop/jam/jam-node/tests/unit/report/data/tiny/"
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
