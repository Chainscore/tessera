from dataclasses import dataclass
import json
import os
from typing import List
from jam.consensus.safrole.errors import SafroleErrorCode
from jam.consensus.safrole.gamma import GammaS, GammaA, GammaK, GammaZ
from jam.state.components.eta import Eta
from jam.state.components.iota import Iota
from jam.state.components.kappa import Kappa
from jam.state.components.lambda_ import Lambda_
from jam.types.base.choices.choice import Choice, decodable_choice
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.block import Block
from jam.types.extrinsics.disputes import Offenders
from jam.types.extrinsics.tickets import TicketsExtrinsic
from jam.types.header import OptionalTicketsMark, OptionalEpochMark
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.jstruct import JsonSerde
from jam.utils.jstruct.decorators import with_json_metadata
from tests.fixtures.dummy_block import create_dummy_block
from jam.state.state import State
from tests.fixtures.dummy_state import create_dummy_state

@decodable_dataclass
@dataclass
class Input(Codable, JsonSerde):
    slot: U32
    entropy: ByteArray32
    extrinsic: TicketsExtrinsic

    def to_block(self) -> Block:
        block = create_dummy_block()
        block.extrinsic.tickets = self.extrinsic
        block.header.slot = self.slot
        optional_entropy_mark = block.header.epoch_mark
        entropy_mark = optional_entropy_mark.get_value()
        entropy_mark.entropy = self.entropy
        optional_entropy_mark = OptionalEpochMark(entropy_mark)
        block.header.epoch_mark = optional_entropy_mark
        return block

@decodable_dataclass
@dataclass
@with_json_metadata(**{
    "lambda_": {
        "name": "lambda"
    }
})
class PreState(Codable, JsonSerde):
    tau: U32
    eta: Eta
    lambda_: Lambda_
    kappa: Kappa
    gamma_k: GammaK
    iota: Iota
    gamma_a: GammaA
    gamma_s: GammaS
    gamma_z: GammaZ
    post_offenders: Offenders

    def to_state(self) -> State:
        state = create_dummy_state()
        state.tau = self.tau
        state.eta = self.eta
        state.lambda_ = self.lambda_
        state.kappa = self.kappa
        state.gamma.k = self.gamma_k
        state.iota = self.iota
        state.gamma.a = self.gamma_a
        state.gamma.s = self.gamma_s
        state.gamma.z = self.gamma_z
        state.psi.o = self.post_offenders
        return state


PostState = PreState

@decodable_dataclass
@dataclass
class OutputMarks(Codable, JsonSerde):
    epoch_mark: OptionalEpochMark
    tickets_mark: OptionalTicketsMark


@decodable_choice
class Output(Choice):
    ok: OutputMarks
    err: SafroleErrorCode


@decodable_dataclass
@dataclass
class Testcase(Codable, JsonSerde):
    input: Input
    pre_state: PreState
    output: Output
    post_state: PostState


def get_testcases_starting_with(prefix: str = "", limit: int = 10) -> List[Testcase]:
    data_dir = "tests/unit/safrole/data/tiny"
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
