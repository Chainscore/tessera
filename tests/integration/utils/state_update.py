from tsrkit_types import Bytes

from jam.execution.pvm.code import Code

from jam.state.state import State
from jam.state.accounts import AccountMetadata

from jam.types.protocol.core import Gas, Balance, BlobLength, ServiceId
from jam.types.protocol.crypto import Hash

from jam.types.state.delta import Ai, Ao, Timestamps, LookupTable

def update_state(state: State):
    pc = bytes(
        [0, 0, 22, 124, 121, 81, 25, 1, 7, 40, 2, 0, 149, 17, 255, 70, 1, 1, 100, 23, 51, 8, 1, 50, 0, 69, 147,
     18])

    c0_authorized_code = [0, 0, 21, 124, 121, 81, 9, 6, 40, 2, 0, 149, 17, 255, 70, 1, 1, 100, 23, 51, 8, 1, 50,
                          0,
                          165, 73, 9]

    code = Code(code=pc, read=b"", r_write=b"", z=0, s=100)
    bytecode = code.encode()
    service_code = Bytes(b"").encode() + bytecode
    code_hash = Hash.blake2b(service_code)

    state.delta[ServiceId(42)].service = AccountMetadata(
        code_hash=code_hash,
        balance=Balance(1_000_000),
        gas_limit=Gas(1_000),
        min_gas=Gas(1_000),
        num_i=Ai(0),
        num_o=Ao(0),
    )
    state.delta[ServiceId(42)].lookup[
        LookupTable(hash=code_hash, length=BlobLength(len(service_code)))] = Timestamps([state.tau])
    state.delta[ServiceId(42)].preimages[code_hash] = service_code

    wi_pc = bytes(
        [0, 0, 90, 51, 12, 149, 27, 0, 112, 254, 124, 117, 6, 40, 2, 200, 199, 3, 149, 51, 7, 200, 203, 4, 130,
         57, 123, 73, 149, 204, 8, 172, 92, 240, 100, 194, 40, 2, 200, 203, 7, 51, 8, 20, 9, 255, 255, 255, 255,
         255, 0, 0, 0, 51, 10, 5, 51, 11, 51, 12, 10, 18, 86, 23, 255, 9, 200, 114, 2, 40, 6, 51, 7, 40, 2, 149,
         23, 0, 112, 254, 100, 40, 10, 19, 149, 23, 0, 112, 254, 51, 8, 50, 0, 133, 148, 164, 146, 74, 1, 164,
         138, 84, 161, 66, 1]
    )

    wi_code = Code(code=wi_pc, read=b"", r_write=b"", z=0, s=(1024 * 100))
    wi_bytecode = wi_code.encode()
    wi_service_code = Bytes(b"").encode() + wi_bytecode
    wi_code_hash = Hash.blake2b(wi_service_code)
    wi_service = ServiceId(1)

    state.delta[wi_service].service = AccountMetadata(
        code_hash=wi_code_hash,
        balance=Balance(1_000_000),
        gas_limit=Gas(1_000),
        min_gas=Gas(1_000),
        num_i=Ai(0),
        num_o=Ao(0),
    )
    state.delta[wi_service].lookup[
        LookupTable(hash=wi_code_hash, length=BlobLength(len(wi_service_code)))] = Timestamps([state.tau])
    state.delta[wi_service].preimages[wi_code_hash] = wi_service_code
