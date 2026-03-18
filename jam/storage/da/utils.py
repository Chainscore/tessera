from typing import Literal

from jam.storage.da import SegmentErasureMap, ErasureAssurerMap
from jam.types.protocol.core import OpaqueHash


def fetch_assurers(root: OpaqueHash, fetch_type: Literal["ERASURE", "SEGMENT"] = "SEGMENT"):
    from jam.settings import settings

    erar_da = ErasureAssurerMap(settings.d3l)

    try:
        if fetch_type == "SEGMENT":
            srer_da = SegmentErasureMap(settings.d3l)
            er_root = srer_da.get(root)
        else:
            er_root = root

        return erar_da.get(er_root)

    except KeyError:
        return None
