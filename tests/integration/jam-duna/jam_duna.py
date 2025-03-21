import asyncio
import json
from dataclasses import dataclass
from typing import Optional


from jam.types.base.choices.option import Option, decodable_option
from jam.__main__ import main
from jam.consensus.safrole.gamma import GammaA, GammaK, GammaS, GammaZ
from jam.state.components.alpha import Alpha
from jam.state.components.chi import ChiA, ChiG, ChiM, ChiV
from jam.state.components.delta import (
    AccountData,
    AccountStorage,
    Delta,
    LookupTimestamps,
    PreImageLookup,
    Timestamps,
)
from jam.state.components.eta import Eta
from jam.state.components.iota import Iota
from jam.state.components.kappa import Kappa
from jam.state.components.lambda_ import Lambda_
from jam.state.components.phi import Phi
from jam.state.components.pi import Pi
from jam.state.components.psi import Psi
from jam.state.components.rho import Rho
from jam.state.components.tau import Tau
from jam.state.components.nu import Nu
from jam.state.components.xi import Xi
from jam.state.state import State
from jam.types.base import Bytes
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.core import U64, Gas, OpaqueHash
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde
from tests.fixtures.dummy_state import create_dummy_state
from tests.unit.recent_history.types import BetaInput
from tests.unit.statistics.types import Pi as TestPi
from jam.utils.json.decorators import with_json_metadata
from jam.types.protocol.core import ServiceId
from jam.types.base.sequences.bytes import ByteArray32
from jam.types.protocol.core import BlobLength

@decodable_dataclass
@dataclass
class DunaGamme(Codable, JsonSerde):
    gamma_k: GammaK
    gamma_a: GammaA
    gamma_s: GammaS
    gamma_z: GammaZ


@decodable_dataclass
@dataclass
class DunaChi(Codable, JsonSerde):
    chi_m: ChiM
    chi_a: ChiA
    chi_v: ChiV
    chi_g: ChiG


@decodable_dataclass
@dataclass
class CustomPreimage(Codable, JsonSerde):
    hash: OpaqueHash
    blob: Bytes


@decodable_vector(CustomPreimage)
class CustomPreimages(Vector): ...


@decodable_vector(U32, 3)
class LookupMetaValue(Vector): ...

@decodable_dataclass
@dataclass
class LookupTable(Codable, JsonSerde):
    hash: ByteArray32
    length: BlobLength

    def __hash__(self) -> int:
        return int.from_bytes(bytes(Hash.sha256(bytes(self.hash) + bytes(self.length))))


@decodable_dataclass
@dataclass
class CustomLookupMeta(Codable, JsonSerde):
    key: LookupTable
    value: Timestamps


@decodable_vector(CustomLookupMeta)
class CustomLookupMetas(Vector): ...


@decodable_dataclass
@dataclass
class CustomService(Codable, JsonSerde):
    code_hash: OpaqueHash
    balance: U64
    min_item_gas: Gas
    min_memo_gas: Gas
    bytes: U64
    items: U32


@decodable_option(AccountStorage)
class OptionStorage(Option): ...


@decodable_dataclass
@dataclass
class CustomAccountData(Codable, JsonSerde):
    preimages: CustomPreimages
    lookup_meta: CustomLookupMetas
    service: CustomService
    storage: OptionStorage


@decodable_dataclass
@dataclass
class Account(Codable, JsonSerde):
    id: ServiceId
    data: CustomAccountData

@decodable_vector(Account)
class DunaDelta(Vector[Account]): ...


@with_json_metadata(
    # alpha={"name": "alpha"},
    lambda_={"name": "lambda", "skip_if_none": True},
    # accounts={"name": "accounts", "skip_if_none": True}
)
@decodable_dataclass
@dataclass
class DunaState(Codable, JsonSerde):
    alpha: Alpha
    varphi: Phi
    beta: BetaInput
    gamma: DunaGamme
    psi: Psi
    eta: Eta
    iota: Iota
    kappa: Kappa
    lambda_: Lambda_
    rho: Rho
    tau: Tau
    chi: DunaChi
    pi: TestPi
    theta: Nu
    xi: Xi
    accounts: DunaDelta

    def to_state(self) -> State:
        state = create_dummy_state()
        state.alpha = self.alpha
        state.phi = self.varphi
        state.beta = self.beta.to_beta()
        state.gamma.k = self.gamma.gamma_k
        state.gamma.a = self.gamma.gamma_a
        state.gamma.s = self.gamma.gamma_s
        state.gamma.z = self.gamma.gamma_z
        state.psi = self.psi
        state.eta = self.eta
        state.iota = self.iota
        state.kappa = self.kappa
        state.lambda_ = self.lambda_
        state.rho = self.rho
        state.tau = self.tau
        state.chi.m = self.chi.chi_m
        state.chi.a = self.chi.chi_a
        state.chi.v = self.chi.chi_v
        state.chi.g = self.chi.chi_g
        state.pi = Pi([self.pi.current, self.pi.last])
        state.theta = self.theta
        state.xi = self.xi

        state.delta = Delta({})

        for i in self.accounts:
            state.delta[i.id] = AccountData(
                storage=AccountStorage({}),
                code_hash=i.data.service.code_hash,
                balance=i.data.service.balance,
                gas_limit=i.data.service.min_item_gas,
                min_gas=i.data.service.min_memo_gas,
                lookup=PreImageLookup({}), #preimages
                timestamps=LookupTimestamps({}), # lookup
            )
            for preimage in i.data.preimages:
                state.delta[i.id].lookup[preimage.hash] = preimage.blob
            for lookup in i.data.lookup_meta:
                # print(LookupTimestamps.get_key(lookup.key.hash,BlobLength(lookup.key.length)))
                state.delta[i.id].timestamps[LookupTimestamps.get_key(lookup.key.hash,BlobLength(lookup.key.length))] = lookup.value
                # state.delta[i.id].timestamps[lookup.key] = lookup.value
            
        return state


genesis_file = "tests/integration/jam-duna/state_snapshots/genesis.json"
with open(genesis_file, "r") as file:
    genesis_data = json.loads(file.read())

    try:
        tc = DunaState.from_json(genesis_data)
        print(f"Decoded {file}")
    except Exception as e:
        print(f"❌ Failed to decode {file}: {e}")

rpc_url = "http://localhost:3001/blocks"
start_slot = 13
initial_state = tc.to_state()




def testState(DunaState,OurState):
    assert(DunaState.alpha==OurState.alpha)
    assert(DunaState.phi==OurState.phi)
    assert(OurState.beta==OurState.beta)
    assert(DunaState.gamma==OurState.gamma)
    assert(DunaState.psi==OurState.psi)
    assert(DunaState.eta==OurState.eta)
    assert(DunaState.iota==OurState.iota)
    assert(DunaState.kappa==OurState.kappa)
    assert(DunaState.lambda_==OurState.lambda_)
    assert(DunaState.rho==OurState.rho)
    assert(DunaState.tau==OurState.tau)
    assert(DunaState.chi==OurState.chi)
    assert(DunaState.pi==OurState.pi)
    assert(DunaState.theta==OurState.nu)
    assert(DunaState.xi==OurState.xi)
    for i in DunaState.delta:
        assert(DunaState.delta[i].storage==OurState.delta[i].storage)
        assert(DunaState.delta[i].lookup==OurState.delta[i].lookup)
        assert(DunaState.delta[i].code_hash==OurState.delta[i].code_hash)
        assert(DunaState.delta[i].balance==OurState.delta[i].balance)
        assert(DunaState.delta[i].gas_limit==OurState.delta[i].gas_limit)
        assert(DunaState.delta[i].min_gas==OurState.delta[i].min_gas)
        assert(DunaState.delta[i].timestamps==OurState.delta[i].timestamps)
    
if __name__ == "__main__":
    transform_state=initial_state.transform()

    our_state=State.detransform(transform_state)
    testState(initial_state,our_state)
    # asyncio.run(main("from jam duna", initial_state, start_slot, rpc_url))

# Command to run file: 'python tests/integration/jam-duna/jam_duna.py'


