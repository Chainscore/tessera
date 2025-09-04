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
    """
    Component: ψ
    Key: 5

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/128c00129600?v=0.7.0
    """

    good: PsiG # g
    bad: PsiB  # b
    wonky: PsiW # w
    offenders: PsiO # o
