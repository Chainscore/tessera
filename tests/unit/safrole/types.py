from dataclasses import dataclass
import os
from typing import List
from jam.state.components.eta import Eta
from jam.state.components.gamma import GammaA, GammaK, GammaS, GammaZ
from jam.state.components.iota import Iota
from jam.state.components.kappa import Kappa
from jam.state.components.lambada import Lambada
from jam.types.base.choices.choice import Choice, decodable_choice
from jam.types.base.choices.option import Option, decodable_option
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.base.string import String
from jam.types.extrinsics.tickets import TicketsExtrinsic
from jam.types.header import OptionalTicketsMark
from jam.types.protocol.crypto import Entropy
from jam.types.protocol.validators import ValidatorArray
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass

@decodable_dataclass
@dataclass
class Input(Codable):
    slot: U32
    entropy: ByteArray32
    extrinsic: TicketsExtrinsic

@decodable_dataclass
@dataclass
class PreState(Codable):
    tau: U32
    eta: Eta
    lambada: Lambada
    kappa: Kappa
    gamma_k: GammaK
    iota: Iota
    gamma_a: GammaA
    gamma_s: GammaS
    gamma_z: GammaZ
    
PostState = PreState

@decodable_dataclass
@dataclass
class EpochMark(Codable):
    """Epoch mark structure."""
    entropy: Entropy
    validators: ValidatorArray

@decodable_option(EpochMark)
class EpochMarkOption(Option): ...

@decodable_dataclass
@dataclass
class EpochMark(Codable):
    """Epoch mark structure."""
    entropy: Entropy
    validators: ValidatorArray

@decodable_dataclass
@dataclass
class OutputMarks(Codable):
    epoch_mark: EpochMarkOption
    tickets_mark: OptionalTicketsMark

@decodable_dataclass
@dataclass
class Error(Codable):
    err: String

@decodable_dataclass
@dataclass
class Ok(Codable):
    ok: OutputMarks

@decodable_choice([Ok, Error])
class Output(Choice): ...

@decodable_dataclass
@dataclass
class Testcase(Codable):
    input: Input
    pre_state: PreState
    output: Output
    post_state: PostState

def get_testcases_starting_with(prefix: str = "", limit: int = 10) -> List[Testcase]:
    data_dir = "tests/unit/safrole/data/tiny"
    result = []
    for index, file in enumerate(os.listdir(data_dir)):
        if index >= limit * 2:
            continue
        elif not file.startswith(prefix):
            continue
        elif file.endswith(".json"):
            continue
        else:
            with open(os.path.join(data_dir, file), "rb") as f:
                data = f.read()
                try:
                    result.append(Testcase.decode_from(data))
                    print(f"✅ Decoded {file}")
                except Exception as e:
                    print(f"❌ Failed to decode {file}: {e}")
                    continue
    return result