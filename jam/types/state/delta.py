from dataclasses import dataclass

from jam.execution.utils import decode_code_hash
from jam.state.utils.key_constructor import construct_state_key
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
    ...


@decodable_dataclass
@dataclass
class LookupTable(Codable, JsonSerde):
    hash: ByteArray32
    length: BlobLength


@decodable_dictionary(ByteArray32, Bytes, key_name="hash", value_name="blob")
class PreImageLookup(Dictionary[ByteArray32, Bytes]):
    """Lookup dictionary"""
    ...


@decodable_vector(element_type=U32, max_length=3)
class Timestamps(Vector[U32]):
    """Lookup timestamps"""
    ...


@decodable_dictionary(ByteArray32, Timestamps)
class LookupTimestamps(Dictionary[ByteArray32, Timestamps]):
    """Lookup timestamps"""
    ...


@decodable_dataclass
@dataclass
class AccountData(Codable, JsonSerde):
    storage: AccountStorage  
    lookup: PreImageLookup # preimages
    timestamps: LookupTimestamps
    code_hash: ServiceCodeHash # code_hash
    balance: Balance # balance
    gas_limit: Gas # min_item_gas
    min_gas: Gas # min_memo_gas

    @property
    def num_i(self):
        return Ai(len(self.storage) + 2 * len(self.lookup))

    @property
    def num_o(self):
        return Ao(
            sum([81 + lookup.length for lookup in self.timestamps]) + sum([32 + len(data) for data in self.storage]))

    def m_c(self) -> (bytes, bytes):
        return decode_code_hash(self.lookup[self.code_hash])

    def historical_lookup(self, timeslot: TimeSlot, preimage_hash: ByteArray32):
        """
            https://graypaper.fluffylabs.dev/#/cc517d7/11c70011e000?v=0.6.5
            """
        if (
                self.lookup[preimage_hash] is not None and
                self.is_preimage_valid(
                    self.timestamps[
                        LookupTable(hash=preimage_hash, length=BlobLength(len(self.lookup[preimage_hash])))],
                    timeslot
                )
        ):
            return self.lookup[preimage_hash]
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
