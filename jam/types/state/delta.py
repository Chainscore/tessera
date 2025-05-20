from dataclasses import dataclass
from typing import Dict

from jam.execution.utils import decode_code_hash
from jam.state.utils.key_constructor import construct_state_key
from jam.types.base import Byte
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.integers.fixed import U32, U64
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.base.sequences.bytes import ByteArray32, Bytes
from jam.types.protocol.core import Balance, BlobLength, Gas, ServiceId, TimeSlot
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.types.protocol.crypto import Hash

ServiceCodeHash = ByteArray32
# TODO - : Confirm these types + usage
"""Number of items in the account storage"""
Ai = U32

"""The total number of octets used in storage"""
Ao = U64

"""The minimum, or threshold, balance needed for any given service account"""
At = Balance


@decodable_dictionary(ByteArray32, Bytes, key_name="key", value_name="value")
class AccountStorage(Dictionary[ByteArray32, Bytes]):
    """Storage dictionary"""
    sid: ServiceId

    def __init__(self, initial: Dict,  service_id: ServiceId):
        self.sid = service_id
        super(Dictionary).__init__(initial)

    def __getitem__(self, key: ByteArray32):
        key = ByteArray32(construct_state_key((self.sid, Bytes(U32(2**32 - 1).encode()) + key[0:23])) + Byte(0))
        return super(Dictionary).__getitem__(key)

    def __setitem__(self, key: ByteArray32, value: Bytes):
        key = ByteArray32(construct_state_key((self.sid, Bytes(U32(2 ** 32 - 1).encode()) + key[0:23])) + Byte(0))
        return super(Dictionary).__setitem__(key, value)




@decodable_dictionary(ByteArray32, Bytes, key_name="hash", value_name="blob")
class AccountPreimages(Dictionary[ByteArray32, Bytes]):
    """ dictionary"""
    sid: ServiceId

    def __init__(self, initial: Dict, service_id: ServiceId):
        self.sid = service_id
        super(Dictionary).__init__(initial)

    def __getitem__(self, key: ByteArray32):
        key = ByteArray32(construct_state_key((self.sid, Bytes(U32(2 ** 32 - 2).encode()) + key[1:24])) + Byte(0))
        return super(Dictionary).__getitem__(key)

    def __setitem__(self, key: ByteArray32, value: Bytes):
        key = ByteArray32(construct_state_key((self.sid, Bytes(U32(2 ** 32 - 2).encode()) + key[1:24])) + Byte(0))
        return super(Dictionary).__setitem__(key, value)


@decodable_vector(element_type=U32, max_length=3)
class Timestamps(Vector[U32]):
    """Lookup timestamps"""
    ...

@decodable_dataclass
@dataclass
class LookupTable(Codable, JsonSerde):
    hash: ByteArray32
    length: BlobLength


@decodable_dictionary(ByteArray32, Timestamps)
class AccountLookup(Dictionary[ByteArray32, Timestamps]):
    """Lookup timestamps"""
    sid: ServiceId

    def __init__(self, initial: Dict, service_id: ServiceId):
        self.sid = service_id
        super(Dictionary).__init__(initial)

    def __getitem__(self, key: LookupTable):
        key = ByteArray32(construct_state_key((self.sid, Bytes(key.length.encode()) + key[2:25])) + Byte(0))
        return super(Dictionary).__getitem__(key)

    def __setitem__(self, key: ByteArray32, value: Timestamps):
        key = ByteArray32(construct_state_key((self.sid, Bytes(key._length.encode() + key[2:25]))) + Byte(0))
        return super(Dictionary).__setitem__(key, value)


@decodable_dataclass
@dataclass
class AccountData(Codable, JsonSerde):
    storage: AccountStorage  
    preimages: AccountPreimages # preimages
    lookup: AccountLookup
    code_hash: ServiceCodeHash # code_hash
    balance: Balance # balance
    gas_limit: Gas # min_item_gas
    min_gas: Gas # min_memo_gas
    num_i: Ai
    num_o: Ao

    def m_c(self) -> (bytes, bytes):
        return decode_code_hash(self.preimages[self.code_hash])

    def historical_lookup(self, timeslot: TimeSlot, preimage_hash: ByteArray32):
        """
        https://graypaper.fluffylabs.dev/#/cc517d7/11c70011e000?v=0.6.5
        """
        if (
                self.preimages[preimage_hash] is not None and
                self.is_preimage_valid(
                    self.lookup[
                        LookupTable(hash=preimage_hash, length=BlobLength(len(self.lookup[preimage_hash])))],
                    timeslot
                )
        ):
            return self.preimages[preimage_hash]
        else:
            return None

    @classmethod
    def is_preimage_valid(cls, lookup_ts: Timestamps, current_ts: TimeSlot):
        """
        https://graypaper.fluffylabs.dev/#/cc517d7/11e700111201?v=0.6.5
        """
        if len(lookup_ts) == 0:
            return False
        elif len(lookup_ts) == 1:
            return lookup_ts[0] < current_ts
        elif len(lookup_ts) == 2:
            return lookup_ts[0] <= current_ts < lookup_ts[1]
        elif len(lookup_ts) == 3:
            return (lookup_ts[0] <= current_ts < lookup_ts[1]) or lookup_ts[2] <= ts
        else:
            raise ValueError("Invalid Timestamp data")


@decodable_dictionary(ServiceId, AccountData, key_name="id", value_name="data")
class Delta(Dictionary[ServiceId, AccountData]):
    """Delta state"""
    ...
