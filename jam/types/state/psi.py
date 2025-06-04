from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from jam.types.protocol.crypto import Ed25519Public, WorkReportHash


PsiG = TypedVector[WorkReportHash]

PsiB = TypedVector[WorkReportHash]

PsiW = TypedVector[WorkReportHash]

PsiO = TypedVector[Ed25519Public]


@structure
class Psi:
    """Disputes state"""

    good: PsiG
    bad: PsiB
    wonky: PsiW
    offenders: PsiO
