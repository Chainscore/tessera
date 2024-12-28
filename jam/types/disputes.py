# """Dispute types for the JAM protocol."""
# from dataclasses import dataclass
# from typing import List
# from .base import U32
# from .core import OpaqueHash, ValidatorIndex, WorkReportHash, Ed25519Public
# from .crypto import Ed25519Signature

# @dataclass
# class Judgement:
#     """Judgement structure."""
#     vote: bool
#     index: ValidatorIndex
#     signature: Ed25519Signature

# @dataclass
# class Verdict:
#     """Verdict structure."""
#     target: OpaqueHash
#     age: U32
#     votes: List[Judgement]

#     def __post_init__(self):
#         # validators_super_majority should be imported from constants
#         if len(self.votes) > 0:  # validators_super_majority
#             raise ValueError("Verdict votes exceed validators super majority")

# @dataclass
# class Culprit:
#     """Culprit structure."""
#     target: WorkReportHash
#     key: Ed25519Public
#     signature: Ed25519Signature

# @dataclass
# class Fault:
#     """Fault structure."""
#     target: WorkReportHash
#     vote: bool
#     key: Ed25519Public
#     signature: Ed25519Signature

# @dataclass
# class DisputesRecords:
#     """Disputes records structure."""
#     good: List[WorkReportHash]  # psi_g
#     bad: List[WorkReportHash]   # psi_b
#     wonky: List[WorkReportHash] # psi_w
#     offenders: List[Ed25519Public]  # psi_o

# @dataclass
# class DisputesExtrinsic:
#     """Disputes extrinsic structure."""
#     verdicts: List[Verdict]
#     culprits: List[Culprit]
#     faults: List[Fault] 