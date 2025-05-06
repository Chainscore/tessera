# from hashlib import blake2b
from jam.state.components.delta import AccountData
# from jam.types.base.integers.fixed import U32, U64
from jam.types.protocol.core import TimeSlot
from jam.types.base.sequences.bytes import ByteArray32
from jam.state.components.delta import Timestamps

def historical_lookup_fn(accountData: AccountData, timeslot: TimeSlot, preimageHash: ByteArray32):
    """
    https://graypaper.fluffylabs.dev/#/cc517d7/11c70011e000?v=0.6.5
    """
    if accountData.lookup[preimageHash] is not None and helper_fn(accountData.timestamps[preimageHash, len(accountData.lookup[preimageHash])], timeslot):
        return accountData.lookup[preimageHash]
    else:
        return None

# def get_keys(d, is_string=False):
#     keys = set()
#     for key in d.keys():
#         try:
#             if not is_string:
#                 numeric_key = int(key)
#                 keys.add(numeric_key)
#             else:
#                 keys.add(key)

#         except (ValueError, TypeError):
#             pass
#     return keys


def helper_fn(lookup_ts: Timestamps, ts: TimeSlot):
    """
    https://graypaper.fluffylabs.dev/#/cc517d7/11e700111201?v=0.6.5
    """
    if len(lookup_ts) == 0:
        return False
    elif len(lookup_ts) == 1:
        return lookup_ts[0] < ts
    elif len(lookup_ts) == 2:
        return lookup_ts[0] <= ts < lookup_ts[1]
    elif len(lookup_ts) == 3:
        return (lookup_ts[0] <= ts < lookup_ts[1]) or lookup_ts[2] <= ts
