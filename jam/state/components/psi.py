from dataclasses import dataclass
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.crypto import Ed25519Public, WorkReportHash
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass

@decodable_vector(element_type=WorkReportHash)
class PsiG(Vector[WorkReportHash]):
    """Good set work report hashes"""
    ...

@decodable_vector(element_type=WorkReportHash)
class PsiB(Vector[WorkReportHash]):
    """Bad set work report hashes"""
    ...

@decodable_vector(element_type=WorkReportHash)
class PsiW(Vector[WorkReportHash]):
    """Wonky set work report hashes"""
    ...

@decodable_vector(element_type=Ed25519Public)
class PsiO(Vector[Ed25519Public]):
    """Offenders"""
    ...

@decodable_dataclass
@dataclass
class Psi(Codable):
    """Disputes state"""
    g: PsiG
    b: PsiB
    w: PsiW
    o: PsiO