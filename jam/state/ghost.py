# WARN: Do not use, this is about to be removed
import json
from typing import List

from rockstore import RockStore
from jam.models.protocol.validators import ValidatorsData
from jam.models.state.alpha import Alpha
from jam.models.state.eta import Eta
from jam.models.state.omega import AllReadyWRs, Omega
from jam.models.state.pi import AllValidatorStats, Pi, AllServiceStats, AllCoreStats
from jam.models.state.psi import Psi, PsiB, PsiG, PsiO, PsiW
from jam.models.state.kappa import Kappa
from jam.models.state.lambda_ import Lambda_
from jam.models.state.rho import Rho, OptionalWorkReportState
from jam.models.state.tau import Tau
from jam.models.state.chi import Chi, ChiZ, ChiA
from jam.models.state.iota import Iota
from jam.models.state.theta import Theta
from jam.models.state.xi import Xi
from jam.models.state.beta import Beta, BetaHistory, BeefyBelt
from jam.models.state.phi import Phi
from jam.models.state.gamma import Gamma, GammaA, GammaP, GammaZ
from jam.models.state.delta import (
    Delta,
    AccountData,
    Timestamps,
    AccountLookup,
    AccountPreimages,
    AccountStorage,
)
from jam.models.state.sigma import Sigma
from jam.models.work import WorkDependencies
from jam.utils.constants import CORE_COUNT, EPOCH_LENGTH
from jam.state.utils import construct_state_key
from jam.models.protocol.crypto import OpaqueHash, Hash
from jam.models.protocol.core import Balance, Gas, ServiceId
from jam.utils.trie.merkle import StateTrie
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U32
from tsrkit_types.null import Null


class GhostState(Sigma):
    def generate_root(self) -> Bytes[32]:
        """Generate the root hash of the state"""
        return StateTrie().merkelize(self.transform())[0]

    @staticmethod
    def from_random(seed=0) -> "GhostState":
        from jam.utils.dummy.dummy_state_comp import create_dummy_state_components

        return GhostState(**create_dummy_state_components())

    def transform(self) -> dict:
        """
        Transform the state into a dictionary as defined in D.2
        Returns:
            dict: A dictionary representation of the state in this format: {bytes -> Bytes}
        """
        services, service_storage, service_preimages, service_lookup = {}, {}, {}, {}
        for i in self.delta:
            l_key, s_key = set(), set()
            for j in self.delta[i].lookup:
                l_key.add(j)
            for j in self.delta[i].storage:
                s_key.add(j)
            services[construct_state_key((255, i))] = Bytes(
                self.delta[i].service.code_hash.encode()
                + self.delta[i].service.balance.encode()
                + self.delta[i].service.gas_limit.encode()
                + self.delta[i].service.min_gas.encode()
                + self.delta[i].service.num_o.encode()
                + self.delta[i].service.num_i.encode()
            )

            for j in self.delta[i].storage:
                service_storage[
                    construct_state_key((i, Bytes(U32(2**32 - 1).encode()) + j[0:23]))
                ] = self.delta[i].storage[j]
            for j in self.delta[i].preimages:
                service_preimages[
                    construct_state_key((i, Bytes(U32(2**32 - 2).encode()) + j[1:24]))
                ] = Bytes(self.delta[i].preimages[j])

            for j in self.delta[i].lookup:
                service_lookup[
                    construct_state_key(
                        (
                            i,
                            Bytes(j.length.encode() + bytes(Hash.blake2b(j.hash))[2:25]),
                        )
                    )
                ] = Bytes(self.delta[i].lookup[j].encode())

        return {
            construct_state_key(1): Bytes(self.alpha.encode()),
            construct_state_key(2): Bytes(self.phi.encode()),
            construct_state_key(3): Bytes(self.beta.encode()),
            construct_state_key(4): Bytes(self.gamma.encode()),
            construct_state_key(5): Bytes(self.psi.encode()),
            construct_state_key(6): Bytes(self.eta.encode()),
            construct_state_key(7): Bytes(self.iota.encode()),
            construct_state_key(8): Bytes(self.kappa.encode()),
            construct_state_key(9): Bytes(self.lambda_.encode()),
            construct_state_key(10): Bytes(self.rho.encode()),
            construct_state_key(11): Bytes(self.tau.encode()),
            construct_state_key(12): Bytes(self.chi.encode()),
            construct_state_key(13): Bytes(self.pi.encode()),
            construct_state_key(14): Bytes(self.omega.encode()),
            construct_state_key(15): Bytes(self.xi.encode()),
            construct_state_key(16): Bytes(self.theta.encode()),
            **services,
            **service_storage,
            **service_preimages,
            **service_lookup,
        }

    @staticmethod
    def detransform(state: dict) -> "GhostState":
        """Inverse of transform"""
        # Loop thru the whole state dict

        # populating the delta
        delta = {}
        for key, value in sorted(state.items(), key=lambda x: x[0], reverse=True):
            # Start with finding all core state components 1-15
            # if (key[0] <= 15) and bytes(key[0:32]) == 0:
            if int(key[0]) <= 15 and int(key[0]) > 0:
                if int(key[0]) == 1:
                    alpha, _ = Alpha.decode_from(bytes(value))
                elif int(key[0]) == 2:
                    phi, _ = Phi.decode_from(bytes(value))
                elif int(key[0]) == 3:
                    beta, _ = Beta.decode_from(bytes(value))
                elif int(key[0]) == 4:
                    gamma, _ = Gamma.decode_from(bytes(value))
                elif int(key[0]) == 5:
                    psi, _ = Psi.decode_from(bytes(value))
                elif int(key[0]) == 6:
                    eta, _ = Eta.decode_from(bytes(value))
                elif int(key[0]) == 7:
                    iota, _ = Iota.decode_from(bytes(value))
                elif int(key[0]) == 8:
                    kappa, _ = Kappa.decode_from(bytes(value))
                elif int(key[0]) == 9:
                    lambda_, _ = Lambda_.decode_from(bytes(value))
                elif int(key[0]) == 10:
                    rho, _ = Rho.decode_from(bytes(value))
                elif int(key[0]) == 11:
                    tau, _ = Tau.decode_from(bytes(value))
                elif int(key[0]) == 12:
                    chi, _ = Chi.decode_from(bytes(value))
                elif int(key[0]) == 13:
                    pi, _ = Pi.decode_from(bytes(value))
                elif int(key[0]) == 14:
                    omega, _ = Omega.decode_from(bytes(value))
                elif int(key[0]) == 15:
                    xi, _ = Xi.decode_from(bytes(value))
                elif int(key[0]) == 16:
                    theta, _ = Theta.decode_from(bytes(value))

            # Then find all services (first byte is 255, rest is service id)
            elif int(key[0]) == 255:
                service_id = int.from_bytes(bytes(Bytes([key[1], key[3], key[5], key[7]])))
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
                    preimages=AccountPreimages({}),
                    lookup=AccountLookup({}),
                    code_hash=Bytes[32](ac),
                    balance=Balance(ab),
                    gas_limit=Gas(ag),
                    min_gas=Gas(am),
                )

            else:
                if Bytes(key[7:0:-2]) == Bytes(2**32 - 1):
                    # populating the storage
                    service_id = int.from_bytes(bytes(Bytes(key[0:7:2])))
                    delta[service_id].storage[
                        Bytes[32](Bytes(key[8:32] + Bytes(bytearray(8))))
                    ] = value
                elif Bytes(key[7:0:-2]) == Bytes(2**32 - 2):
                    # populating the lookup
                    service_id = int.from_bytes(bytes(Bytes(key[0:7:2])))
                    delta[service_id].lookup[Hash.blake2b(value)] = value

                else:
                    # populating the timestamps
                    service_id = int.from_bytes(bytes(Bytes(key[0:7:2])))
                    TimeStamps, _ = Timestamps.decode_from(bytes(value))
                    timestamp_key = Bytes[32](
                        Bytes(key[1:8:2]) + Bytes(key[8:32]) + Bytes(bytearray(4))
                    )
                    delta[service_id].timestamps[timestamp_key] = TimeStamps

        return GhostState(
            alpha=alpha,
            phi=phi,
            beta=beta,
            theta=theta,
            gamma=gamma,
            psi=psi,
            eta=eta,
            iota=iota,
            kappa=kappa,
            lambda_=lambda_,
            rho=rho,
            tau=tau,
            chi=chi,
            pi=pi,
            omega=omega,
            xi=xi,
            delta=delta,
        )

    @staticmethod
    def genesis(genesis_path="genesis.json") -> "GhostState":
        """Generate the genesis state"""
        from jam.state.transitions.safrole.safrole import Safrole

        gen = json.load(open(genesis_path))
        peers = ValidatorsData.from_json(gen["peers"])
        fallback = Safrole.arrange_fallback(Bytes[32](bytes(32)), peers)

        return GhostState(
            alpha=Alpha.from_json(gen["state"]["auth_pool"]),
            beta=Beta(h=BetaHistory([]), b=BeefyBelt([])),
            theta=Theta([]),
            gamma=Gamma(a=GammaA([]), p=GammaP(peers), s=fallback, z=GammaZ(bytes(144))),
            delta=Delta.from_json(gen["state"]["accounts"]),
            eta=Eta.from_json(gen["state"]["entropy"]),
            iota=Iota(peers),
            kappa=Kappa(peers),
            lambda_=Lambda_(peers),
            rho=Rho([OptionalWorkReportState(Null) for _ in range(CORE_COUNT)]),
            tau=Tau(0),
            phi=Phi.from_json(gen["state"]["auth_queue"]),
            chi=Chi(
                chi_m=ServiceId(0),
                chi_a=ChiA([ServiceId(0) for _ in range(CORE_COUNT)]),
                chi_v=ServiceId(0),
                chi_r=ServiceId(0),
                chi_z=ChiZ({})
            ),
            psi=Psi(good=PsiG([]), bad=PsiB([]), wonky=PsiW([]), offenders=PsiO([])),
            pi=Pi(
                vals_current=AllValidatorStats.empty(),
                vals_last=AllValidatorStats.empty(),
                cores=AllCoreStats.empty(),
                services=AllServiceStats({}),
            ),
            omega=Omega([AllReadyWRs([]) for _ in range(EPOCH_LENGTH)]),
            xi=Xi([WorkDependencies([]) for _ in range(EPOCH_LENGTH)]),
        )

    def save(self, db: RockStore):
        data = self.transform()
        for key, value in data.items():
            db.put(bytes(key), bytes(value))

    @staticmethod
    def load(db: RockStore, keys: List[Bytes[32]] = []) -> "GhostState":
        data = {}
        service_ids: set[ServiceId] = set()

        for i in range(1, 16):
            state_key = construct_state_key(i)
            data[state_key] = Bytes(db.get(bytes(state_key)))
        for key in keys:
            if int.from_bytes(bytes(Bytes([key[0], key[2], key[4], key[6]]))) not in service_ids:
                service_ids.add(
                    ServiceId(int.from_bytes(bytes(Bytes([key[0], key[2], key[4], key[6]]))))
                )
            data[key] = Bytes(db.get(bytes(key)))
        for service_id in service_ids:
            service_key = construct_state_key((255, service_id))
            data[service_key] = Bytes(db.get(bytes(service_key)))

        return GhostState.detransform(data)
