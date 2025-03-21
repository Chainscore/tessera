from dataclasses import dataclass


from jam.consensus.safrole.gamma import GammaA, GammaK, GammaS, GammaZ
from jam.state.components.alpha import Alpha
from jam.state.components.chi import ChiA, ChiG, ChiM, ChiV
from jam.state.components.delta import (
    AccountData,
    AccountStorage,
    Delta,
    LookupTable,
    LookupTimestamps,
    PreImageLookup,
    Timestamps,
)
from jam.state.components.eta import Eta
from jam.state.components.iota import Iota
from jam.state.components.kappa import Kappa
from jam.state.components.lambda_ import Lambda_

from jam.state.components.nu import Nu
from jam.state.components.phi import Phi
from jam.state.components.pi import Pi
from jam.state.components.psi import Psi
from jam.state.components.rho import Rho
from jam.state.components.tau import Tau

from jam.state.components.xi import Xi
from jam.state.state import State
from jam.types.base import Bytes
from jam.types.base.choices.option import Option, decodable_option

from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.core import U64, Gas, OpaqueHash
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde

from jam.utils.json.decorators import with_json_metadata

from tests.fixtures.dummy_state import create_dummy_state
from tests.unit.recent_history.types import BetaInput as TestBeta
from tests.unit.statistics.types import Pi as TestPi


@decodable_dataclass
@dataclass
class DunaGamma(Codable, JsonSerde):
    k: GammaK
    a: GammaA
    s: GammaS
    z: GammaZ
      

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


@with_json_metadata(
    preimages={"skip_if_none": True},
    lookup_meta={"skip_if_none": True},
    service={"skip_if_none": True},
    storage={"skip_if_none": True},
)

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
    id: U32
    data: CustomAccountData


@decodable_vector(Account)
class DunaDelta(Vector): ...


@with_json_metadata(
    alpha={"skip_if_none": True},
    varphi={"skip_if_none": True},
    beta={"skip_if_none": True},
    gamma={"skip_if_none": True},
    psi={"skip_if_none": True},
    eta={"skip_if_none": True},
    iota={"skip_if_none": True},
    kappa={"skip_if_none": True},
    lambda_={"name": "lambda", "skip_if_none": True},
    rho={"skip_if_none": True},
    tau={"skip_if_none": True},
    chi={"skip_if_none": True},
    pi={"skip_if_none": True},
    nu={"skip_if_none": True},
    xi={"skip_if_none": True},
    accounts={"skip_if_none": True},
)
@decodable_dataclass
@dataclass
class GeneralState(Codable, JsonSerde):
    alpha: Alpha
    varphi: Phi
    beta: TestBeta
    gamma: DunaGamma
    psi: Psi
    eta: Eta
    iota: Iota
    kappa: Kappa
    lambda_: Lambda_
    rho: Rho
    tau: Tau
    chi: DunaChi
    pi: TestPi
    nu: Nu
    xi: Xi
    accounts: DunaDelta

    # TODO: Fix parsing error when Delta incomplete

    def to_state(self) -> State:
        state = create_dummy_state()

        if self.alpha:
            state.alpha = self.alpha

        if self.varphi:
            state.phi = self.varphi

        if self.beta:
            state.beta = self.beta.to_beta()

        if self.gamma:

            state.gamma.k = self.gamma.k
            state.gamma.a = self.gamma.a
            state.gamma.s = self.gamma.s
            state.gamma.z = self.gamma.z


        if self.psi:
            state.psi = self.psi

        if self.eta:
            state.eta = self.eta

        if self.iota:
            state.iota = self.iota

        if self.kappa:
            state.kappa = self.kappa

        if self.lambda_:
            state.lambda_ = self.lambda_

        if self.rho:
            state.rho = self.rho

        if self.tau:
            state.tau = self.tau

        if self.chi:
            state.chi.m = self.chi.chi_m
            state.chi.a = self.chi.chi_a
            state.chi.v = self.chi.chi_v
            state.chi.g = self.chi.chi_g

        if self.pi:
            state.pi = Pi([self.pi.current, self.pi.last])

        if self.nu:
            state.nu = self.nu

        if self.xi:
            state.xi = self.xi

        if self.accounts:
            state.delta = Delta({})

            for i in self.accounts:
                state.delta[i.id] = AccountData(
                    storage=AccountStorage({}),
                    code_hash=i.data.service.code_hash,
                    balance=i.data.service.balance,
                    gas_limit=i.data.service.min_item_gas,
                    min_gas=i.data.service.min_memo_gas,
                    lookup=PreImageLookup({}),
                    timestamps=LookupTimestamps({}),
                )
                for preimage in i.data.preimages:
                    state.delta[i.id].lookup[preimage.hash] = preimage.blob
                for lookup in i.data.lookup_meta:
                    state.delta[i.id].timestamps[lookup.key] = lookup.value

        return state
