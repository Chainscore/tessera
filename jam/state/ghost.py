import json
from typing import List
from jam.db.kv import KVStore
from jam.types import Null
from jam.types.protocol.validators import IPAddress, ValidatorMetadata, ValidatorName, ValidatorData, ValidatorsData
from jam.types.state import (
    Alpha, AuthorizationPool,
    AuthorizationQueue, AuthorizerHash, Phi,
    Beta,
    Eta,
    AllValidatorStats, Pi, ValidatorStat, AllServiceStats, AllCoreStats, CoreStat,
    Psi, PsiB, PsiG, PsiO, PsiW,
    Kappa,
    Lambda_,
    OptionalWorkReportState, Rho,
    Tau,
    Chi, ChiG,
    Iota,
    AllReadyWRs, Nu,
    Xi,
    Gamma, GammaA, GammaK, GammaZ,
    AccountData,
    AccountStorage,
    Delta,
    LookupTimestamps,
    PreImageLookup,
    Timestamps,
)
from jam.types.state.sigma import Sigma
from jam.types.work.report import WorkDependencies
from jam.utils.constants import CORE_COUNT, VALIDATOR_COUNT, MAX_AUTH_QUEUE_ITEMS, EPOCH_LENGTH
from jam.state.utils.key_constructor import construct_state_key
from jam.types.base.sequences.bytes import ByteArray32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base.integers.fixed import U64, U32, U8, U16
from jam.types.protocol.crypto import OpaqueHash, Hash, BlsPublic, Ed25519Public, BandersnatchPublic
from jam.types.protocol.core import Balance, Gas, ServiceId
from jam.state.merkle import StateTrie
from jam.consensus.safrole.safrole import Safrole


class GhostState(Sigma):

    def generate_root(self) -> ByteArray32:
        """Generate the root hash of the state"""
        return StateTrie().merkelize(self.transform())[0]

    @staticmethod
    def from_random(seed = 0) -> "GhostState":
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
            construct_state_key(14): Bytes(self.nu.encode()),
            construct_state_key(15): Bytes(self.xi.encode()),
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
                    nu, _ = Nu.decode_from(bytes(value))
                elif int(key[0]) == 15:
                    xi, _ = Xi.decode_from(bytes(value))

            # Then find all services (first byte is 255, rest is service id)
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

        return GhostState(
            alpha=alpha,
            phi=phi,
            beta=beta,
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
            nu=nu,
            xi=xi,
            delta=delta,
        )

    @staticmethod
    def genesis(genesis_path = "genesis.json") -> "GhostState":
        """Generate the genesis state"""
        peers = ValidatorsData.from_json(json.load(open(genesis_path))["peers"])
        empty_set = [ValidatorData(
            bandersnatch=BandersnatchPublic(bytes(32)),
            ed25519=Ed25519Public(bytes(32)),
            bls=BlsPublic(bytes(144)),
            metadata=ValidatorMetadata(ValidatorName(""), IPAddress([U8(127), U8(0), U8(0), U8(1)]), U16(0))
        ) for _ in range(VALIDATOR_COUNT)]
        fallback = Safrole.arrange_fallback(ByteArray32(bytes(32)), peers)

        return GhostState(
            alpha=Alpha([AuthorizationPool([]) for _ in range(CORE_COUNT)]),
            beta=Beta([]),
            gamma=Gamma(a=GammaA([]), k=GammaK(peers.value), s=fallback, z=GammaZ(bytes(144))),
            delta=Delta({}),
            eta=Eta([ByteArray32(bytes(32)) for _ in range(4)]),
            iota=Iota(empty_set),
            kappa=Kappa(peers.value),
            lambda_=Lambda_(empty_set),
            rho=Rho([OptionalWorkReportState(Null) for _ in range(CORE_COUNT)]),
            tau=Tau(0),
            phi=Phi([AuthorizationQueue([AuthorizerHash(bytes(32)) for _ in range(MAX_AUTH_QUEUE_ITEMS)]) for _ in range(CORE_COUNT)]),
            chi=Chi(chi_m=ServiceId(0), chi_a=ServiceId(0), chi_v=ServiceId(0), chi_g=ChiG({})),
            psi=Psi(good=PsiG([]), bad=PsiB([]), wonky=PsiW([]), offenders=PsiO([])),
            pi=Pi(
                vals_current=AllValidatorStats([ValidatorStat(blocks=U32(0), tickets=U32(0), pre_images=U32(0), pre_images_size=U32(0), guarantees=U32(0), assurances=U32(0)) for _ in range(VALIDATOR_COUNT)]),
                vals_last=AllValidatorStats([ValidatorStat(blocks=U32(0), tickets=U32(0), pre_images=U32(0), pre_images_size=U32(0), guarantees=U32(0), assurances=U32(0)) for _ in range(VALIDATOR_COUNT)]),
                cores=AllCoreStats([CoreStat(gas_used=U32(0), imports=U32(0), extrinsic_count=U32(0), extrinsic_size=U32(0), exports=U32(0), bundle_size=U32(0), da_load=U32(0), popularity=U32(0)) for _ in range(CORE_COUNT)]),
                services=AllServiceStats({})
            ),
            nu=Nu([AllReadyWRs([]) for _ in range(EPOCH_LENGTH)]),
            xi=Xi([WorkDependencies([]) for _ in range(EPOCH_LENGTH)]),
        )

    def save(self, db: KVStore):
        data = self.transform()
        for key, value in data.items():
            db.put(bytes(key), bytes(value))

    @staticmethod
    def load(db: KVStore, keys: List[ByteArray32] = []) -> "GhostState":
        data = {}
        service_ids: set[ServiceId] = set()

        for i in range(1, 16):
            state_key = construct_state_key(i)
            # print(type(state_key))
            data[state_key] = Bytes(db.get(bytes(state_key)))
        for key in keys:
            if int.from_bytes(
                    bytes(Bytes([key[0], key[2], key[4], key[6]]))
            ) not in service_ids:
                service_ids.add(ServiceId(int.from_bytes(
                    bytes(Bytes([key[0], key[2], key[4], key[6]]))
                )))
            data[key] = Bytes(db.get(bytes(key)))
        for service_id in service_ids:
            service_key = construct_state_key((255, service_id))
            data[service_key] = Bytes(db.get(bytes(service_key)))

        return GhostState.detransform(data)
