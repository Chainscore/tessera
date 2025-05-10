from hashlib import blake2b
from jam.types.state.delta import AccountData
from jam.types.base.integers.fixed import U32, U64


def historical_look_up(a: AccountData, t: U32, h):
    byte_value = bytes.fromhex(h[2:])
    hashed = "0x" + blake2b(byte_value, digest_size=32).hexdigest()
    if hashed in get_keys(a.lookup, True) and util_i(a.timestamps[h, a.lookup[hashed]], t):
        return a.lookup[hashed]
    else:
        return None


def get_keys(d, is_string=False):
    keys = set()
    for key in d.keys():
        try:
            if not is_string:
                numeric_key = int(key)
                keys.add(numeric_key)
            else:
                keys.add(key)

        except (ValueError, TypeError):
            pass
    return keys


def util_i(_l, t):
    if len(_l) == 0:
        return False
    elif len(_l) == 1:
        return _l[0] < t
    elif len(_l) == 2:
        return _l[0] <= t < _l[1]
    elif len(_l) == 3:
        return (_l[0] <= t < _l[1]) or _l[2] <= t
