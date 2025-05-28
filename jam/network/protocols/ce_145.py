from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.types import Int, BitArray, Boolean
from jam.types.base import bit
from jam.types.base.sequences.bytes import bit_array
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from dataclasses import dataclass
from jam.utils.json import JsonSerde
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature, Hash



@decodable_dataclass
@dataclass
class CE145Data(Codable, JsonSerde):
    epoch_index: Int
    validator_index: Int
    validity: Boolean
    work_report_hash: WorkReportHash
    ed25519_signature: Ed25519Signature

class JudgmentPublication(NetworkProtocol):
    """
    CE 144 Protocol (Judgment Publication ) => Announcement of judgement.

    Protocol Flow:
        Auditor -> Validator

        --> Epoch Index ++ Validator Index  ++ Validity ++ Work-report Hash ++ Ed25529 Signature
        --> FIN
        <-- FIN

    sources:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-145-judgment-publication

    """
    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE145