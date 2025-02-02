from dataclasses import dataclass
import json
import os
from typing import List
from jam.state.components.eta import Eta
from jam.state.components.gamma import GammaA, GammaK, GammaZ
from jam.state.components.iota import Iota
from jam.state.components.kappa import Kappa
from jam.state.components.lambada import Lambada
from jam.types.base.choices.choice import Choice, decodable_choice
from jam.types.base.choices.option import Option, decodable_option
from jam.types.base.enum import Enum, decodable_enum
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.extrinsics.disputes import Offenders
from jam.types.extrinsics.tickets import TicketsExtrinsic
from jam.types.header import OptionalTicketsMark
from jam.types.protocol.crypto import Entropy
from jam.types.protocol.validators import ValidatorArray
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass
from jam.utils.constants import EPOCH_LENGTH
from jam.types.protocol.crypto import BandersnatchPublic
from jam.types.extrinsics.tickets import TicketBody
from jam.types.base.sequences.array import Array, decodable_array

@decodable_dataclass
@dataclass
class Input(Codable):
    slot: U32
    entropy: ByteArray32
    extrinsic: TicketsExtrinsic

@decodable_array(length=EPOCH_LENGTH, element_type=TicketBody)
class GammaSTickets(Array[TicketBody]):
    """Current epoch's slot sealers: set of highest scoring ticket ids for this epoch"""
    ...

@decodable_array(length=EPOCH_LENGTH, element_type=BandersnatchPublic)
class GammaSFallback(Array[BandersnatchPublic]):
    """Fallback set of slot sealers: set of public keys of the slot sealers for this epoch"""
    ...

@decodable_choice
class GammaS(Choice):
    """Either the current epoch's slot sealers or the fallback set of slot sealers"""
    tickets: GammaSTickets
    keys: GammaSFallback


@decodable_dataclass
@dataclass
class PreState(Codable):
    tau: U32
    eta: Eta
    lambda: Lambada
    kappa: Kappa
    gamma_k: GammaK
    iota: Iota
    gamma_a: GammaA
    gamma_s: GammaS
    gamma_z: GammaZ
    post_offenders: Offenders
    
PostState = PreState

@decodable_dataclass
@dataclass
class EpochMark(Codable):
    """Epoch mark structure."""
    entropy: Entropy
    tickets_entropy: Entropy
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

@decodable_enum
class ErrorType(Enum):
    BAD_SLOT = "bad_slot"
    UNEXPECTED_TICKET = "unexpected_ticket"
    BAD_TICKET_ORDER = "bad_ticket_order"
    BAD_TICKET_PROOF = "bad_ticket_proof"
    BAD_TICKET_ATTEMPT = "bad_ticket_attempt"
    RESERVED = "reserved"
    DUPLICATE_TICKET = "duplicate_ticket"

@decodable_choice
class Output(Choice): 
    ok: OutputMarks
    err: ErrorType

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
                    result.append(tc)
                    print(f"✅ Decoded {file}")
                except Exception as e:
                    print(f"❌ Failed to decode {file}: {e}")
                    continue
    return result