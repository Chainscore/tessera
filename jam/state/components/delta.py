from dataclasses import dataclass
from jam.config.settings import settings
from jam.state.utils.key_constructor import construct_state_key
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.integers.fixed import U32, U64
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.base.sequences.bytes import ByteArray32, Bytes
from jam.types.protocol.core import Balance, BlobLength, Gas, ServiceId
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.types.protocol.crypto import Hash
from jam.state.components.phi import Phi
from jam.state.components.chi import Chi

ServiceCodeHash = ByteArray32

@decodable_dictionary(ByteArray32, Bytes)
class AccountStorage(Dictionary[ByteArray32, Bytes]):
    """Storage dictionary"""

    ...


@decodable_dictionary(ByteArray32, Bytes)
class PreImageLookup(Dictionary[ByteArray32, Bytes]):
    """Lookup dictionary"""

    ...


@decodable_dataclass
@dataclass
class LookupTable(Codable, JsonSerde):
    hash: ByteArray32
    length: BlobLength

    def __hash__(self) -> int:
        return int.from_bytes(bytes(Hash.sha256(bytes(self.hash) + bytes(self.length))))

@decodable_vector(element_type=U32, max_length=3)
class Timestamps(Vector[U32]):
    """Lookup timestamps"""
    ...

@decodable_dictionary(LookupTable, Timestamps)
class LookupTimestamps(Dictionary[LookupTable, Timestamps]):
    """Lookup timestamps"""

    @staticmethod
    def get_key(hash: ByteArray32, length: BlobLength) -> ByteArray32:
        return ByteArray32(Bytes(length.encode()) + Hash.blake2b(hash)[2:26] + Bytes(bytearray(4)))

    @staticmethod
    def get_length(hash: ByteArray32) -> BlobLength:
        return BlobLength(int.from_bytes(bytes(Bytes(hash[0:4])), byteorder='little'))
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


@decodable_dictionary(ServiceId, AccountData)
class Delta(Dictionary[ServiceId, AccountData]):
    """Delta state"""
    
    def __contains__(self, key: int|ServiceId):
        return bool(settings.db.get(construct_state_key(255, key)) is not None)

    def __getitem__(self, key):
        

    def transform(self):
        services, service_storage, service_preimages, service_lookup = {}, {}, {}, {}
        for i in self.delta:
            l_key, s_key = set(), set()
            for j in self.delta[i].timestamps:
                l_key.add(j)
            for j in self.delta[i].storage:
                s_key.add(j)
            a_i = 2 * len(list(l_key)) + len(list(s_key))
            a_s, a_l = 0, 0
            if l_key:
                for key in l_key:
                    # fetching the length from the LookupTimestamps
                    a_l += 81 + int(LookupTimestamps.get_length(key))
            if s_key:
                for key in s_key:
                    a_s += 32 + len(self.delta[i].storage[key])

            services[construct_state_key((255, i))] = Bytes(
                self.delta[i].code_hash.encode()
                + self.delta[i].balance.encode()
                + self.delta[i].gas_limit.encode()
                + self.delta[i].min_gas.encode()
                + U64(a_l + a_s).encode()
                + U32(a_i).encode()
            )

            for j in self.delta[i].storage:
                service_storage[
                    construct_state_key(
                        (i, ByteArray32(Bytes(U32(2**32 - 1).encode()) + j[0:28]))
                    )
                ] = self.delta[i].storage[j]
            for j in self.delta[i].lookup:
                service_preimages[
                    construct_state_key(
                        (i, ByteArray32(Bytes(U32(2**32 - 2).encode()) + j[1:29]))
                    )
                ] = Bytes(self.delta[i].lookup[j])

            for j in self.delta[i].timestamps:
                service_lookup[construct_state_key((i, j))] = Bytes(
                    self.delta[i].timestamps[j].encode()
                )
        return services, service_storage, service_preimages, service_lookup
    
    @staticmethod
    def detransform(state: dict) -> "Delta":
                # populating the delta
        delta = {}
        for key, value in sorted(state.items(), key=lambda x: x[0], reverse=True):
            # Then find all services (first byte is 255, rest is service id)
            if int(key[0]) <= 15 and int(key[0]) > 0:
                continue
            elif int(key[0]) == 255:
                service_id = int.from_bytes(
                    bytes(Bytes([key[1], key[3], key[5], key[7]]))
                )
                total_offset = 0
                ac, offset = OpaqueHash.decode_from(bytes(value), total_offset)
                total_offset += offset
                ab, offset = Balance.decode_from(bytes(value), total_offset)
                total_offset += offset
                ag, offset = Gas.decode_from(bytes(value), total_offset)
                total_offset += offset
                am, offset = Gas.decode_from(bytes(value), total_offset)
                total_offset += offset
                ao, offset = Gas.decode_from(bytes(value), total_offset)
                total_offset += offset
                ai, offset = U32.decode_from(bytes(value), total_offset)
                total_offset += offset
                delta[service_id] = AccountData(
                    storage=AccountStorage({}),
                    lookup=PreImageLookup({}),
                    timestamps=LookupTimestamps({}),
                    code_hash=ByteArray32(ac),
                    balance=Balance(ab),
                    gas_limit=Gas(ag),
                    min_gas=Gas(am),
                )

            else:
                if Bytes(key[7:0:-2]) == Bytes(2**32 - 1):
                    # populating the storage
                    service_id = int.from_bytes(bytes(Bytes(key[0:7:2])))
                    delta[service_id].storage[
                        ByteArray32(Bytes(key[8:32] + Bytes(bytearray(8))))
                    ] = value
                elif Bytes(key[7:0:-2]) == Bytes(2**32 - 2):
                    # populating the lookup
                    service_id = int.from_bytes(bytes(Bytes(key[0:7:2])))
                    delta[service_id].lookup[Hash.blake2b(value)] = value

                else:
                    # populating the timestamps
                    service_id = int.from_bytes(bytes(Bytes(key[0:7:2])))
                    TimeStamps, _ = Timestamps.decode_from(bytes(value))
                    timestamp_key = ByteArray32(
                        Bytes(key[1:8:2]) + Bytes(key[8:32]) + Bytes(bytearray(4))
                    )
                    delta[service_id].timestamps[timestamp_key] = TimeStamps
        return Delta(delta)


# TODO - : Confirm these types + usage
"""Number of items in the account storage"""
Ai = U32

"""The total number of octets used in storage"""
Ao = U64

"""The minimum, or threshold, balance needed for any given service account"""
At = Balance
