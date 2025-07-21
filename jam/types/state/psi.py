from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from jam.types.protocol.crypto import Ed25519Public, WorkReportHash


class PsiG(TypedVector[WorkReportHash]):
    ...


class PsiB(TypedVector[WorkReportHash]):
    ...


class PsiW(TypedVector[WorkReportHash]):
    ...


class PsiO(TypedVector[Ed25519Public]):
    ...


# State key: 5
@structure
class Psi:
    """Disputes state"""

    good: PsiG
    bad: PsiB
    wonky: PsiW
    offenders: PsiO
