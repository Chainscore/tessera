from dataclasses import dataclass
from typing import Optional

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
from jam.state.components.phi import Phi
from jam.state.components.pi import Pi
from jam.state.components.psi import Psi
from jam.state.components.rho import Rho
from jam.state.components.tau import Tau
from jam.state.components.theta import Theta
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
from tests.unit.recent_history.types import BetaInput as TestBeta
from tests.unit.statistics.types import Pi as TestPi


@decodable_dataclass
@dataclass
class DunaGamma(Codable, JsonSerde):
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


@decodable_dataclass
@dataclass
class CustomAccountData(Codable, JsonSerde):
    preimages: CustomPreimages
    lookup_meta: CustomLookupMetas
    service: CustomService
    storage: Optional[AccountStorage] = None


@decodable_dataclass
@dataclass
class Account(Codable, JsonSerde):
    id: U32
    data: CustomAccountData


@decodable_vector(Account)
class DunaDelta(Vector): ...


@decodable_dataclass
@dataclass
class GeneralState(Codable, JsonSerde):
    alpha: Optional[Alpha] = None
    varphi: Optional[Phi] = None
    beta: Optional[TestBeta] = None
    gamma: Optional[DunaGamma] = None
    psi: Optional[Psi] = None
    eta: Optional[Eta] = None
    iota: Optional[Iota] = None
    kappa: Optional[Kappa] = None
    lambda_: Optional[Lambda_] = None
    rho: Optional[Rho] = None
    tau: Optional[Tau] = None
    chi: Optional[DunaChi] = None
    pi: Optional[TestPi] = None
    theta: Optional[Theta] = None
    xi: Optional[Xi] = None
    accounts: Optional[DunaDelta] = None

    def to_state(self) -> State:
        state = create_dummy_state()

        if self.alpha:
            state.alpha = self.alpha

        if self.varphi:
            state.phi = self.varphi

        if self.beta:
            state.beta = self.beta.to_beta()

        if self.gamma:
            state.gamma.k = self.gamma.gamma_k
            state.gamma.a = self.gamma.gamma_a
            state.gamma.s = self.gamma.gamma_s
            state.gamma.z = self.gamma.gamma_z

        if self.psi:
            state.psi = self.psi

        if self.eta:
            state.eta = self.eta

        if self.iota:
            state.iota = self.iota

        if self.kappa:
            state.kappa = self.kappa

        if self.lambda__:
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

        if self.theta:
            state.theta = self.theta

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
