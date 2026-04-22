from typing import Self
from jam.block.extrinsics.disputes import DisputesExtrinsic
from jam.models.protocol.crypto import Ed25519Public
from tsrkit_types import TypedVector


class OffendersMark(TypedVector[Ed25519Public]):
    @classmethod
    def produce(cls, disputes: DisputesExtrinsic) -> Self:
        """
        Returns the offenders mark for all new disputes reported. Get all the keys of culprits and faults
        and return the offenders mark.
        https://graypaper.fluffylabs.dev/#/68eaa1f/131c00131c00?v=0.6.4
        """
        c_keys = [culprit.key for culprit in disputes.culprits]
        f_keys = [fault.key for fault in disputes.faults]
        offenders = list(set(c_keys + f_keys))
        return cls(offenders)
