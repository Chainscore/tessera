from jam.db.kv import KVStore
from jam.state.components.alpha import Alpha, AuthorizationPool
from jam.state.components.eta import Eta
from jam.state.components.pi import AllValidatorStats, Pi, ValidatorStat
from jam.state.components.psi import Psi, PsiB, PsiG, PsiO, PsiW
from jam.state.components.kappa import Kappa
from jam.state.components.lambda_ import Lambda_
from jam.state.components.rho import OptionalWorkReportState, Rho
from jam.state.components.tau import Tau
from jam.state.components.chi import Chi, ChiG
from jam.state.components.sigma import Sigma
from jam.state.components.iota import Iota
from jam.state.components.nu import AllReadyWRs, Nu
from jam.state.components.xi import Xi
from jam.state.merkle import StateMerkle
from jam.state.utils.key_constructor import construct_state_key
from jam.state.components.phi import AuthorizationQueue, AuthorizerHash, Phi
from jam.state.components.beta import Beta
from jam.consensus.safrole.gamma import Gamma, GammaA, GammaK, GammaS, GammaZ
from jam.types.base.integers.fixed import U64, U32
from jam.types.base.null import Null
from jam.types.base.sequences.bytes import ByteArray32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.protocol.core import Balance, BlobLength, Gas, ServiceId
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic, Ed25519Public, Hash
from jam.types.protocol.crypto import OpaqueHash
from jam.state.components.delta import (
    AccountData,
    AccountStorage,
    Delta,
    LookupTimestamps,
    PreImageLookup,
    Timestamps,
)
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata
from jam.types.work.report import WorkDependencies
from jam.utils.constants import CORE_COUNT, EPOCH_LENGTH, MAX_AUTH_QUEUE_ITEMS, VALIDATOR_COUNT


class State(Sigma):
    """
    State implementation that 
        - Extends Sigma
        - Adds Merklization (generates root, get_merkle_nodes)
        - Adds transform and detransform methods

    Args:
        **kwargs: Keyword arguments for the components of the state
    """

    def __init__(self, **kwargs):
        """Initialize state with component kwargs"""
        super().__init__(**kwargs)
        self._merkle = StateMerkle(Hash.blake2b)

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
    def detransform(state: dict) -> "State":
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
                    print("Storage")
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

        return State(
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

    def generate_root(self) -> ByteArray32:
        """Generate the root hash of the state"""
        return self._merkle.merkelize(self.transform())

    def get_merkle_nodes(self) -> dict:
        """Get all nodes in the state Merkle trie"""
        return self._merkle.get_nodes()
    
    @staticmethod
    def genesis(peers: list[ValidatorData], fallback: GammaS) -> "State":
        """Generate the genesis state"""

        empty_validators = [ValidatorData(
            bandersnatch=BandersnatchPublic(bytes(32)),
            ed25519=Ed25519Public(bytes(32)),
            bls=BlsPublic(bytes(144)),
            metadata=ValidatorMetadata(bytes(128))
        ) for _ in range(VALIDATOR_COUNT)]

        return State(
            alpha=Alpha([AuthorizationPool([]) for _ in range(CORE_COUNT)]),
            beta=Beta([]),
            gamma=Gamma(a=GammaA([]), k=GammaK(peers), s=fallback, z=GammaZ(bytes(144))),
            delta=Delta({}),
            eta=Eta([ByteArray32(bytes(32)) for _ in range(4)]),
            iota=Iota(empty_validators),
            kappa=Kappa(peers),
            lambda_=Lambda_(empty_validators),
            rho=Rho([OptionalWorkReportState(Null) for _ in range(CORE_COUNT)]),
            tau=Tau(0),
            phi=Phi([AuthorizationQueue([AuthorizerHash(bytes(32)) for _ in range(MAX_AUTH_QUEUE_ITEMS)]) for _ in range(CORE_COUNT)]),
            chi=Chi(chi_m=ServiceId(0), chi_a=ServiceId(0), chi_v=ServiceId(0), chi_g=ChiG({})),
            psi=Psi(good=PsiG([]), bad=PsiB([]), wonky=PsiW([]), offenders=PsiO([])),
            pi=Pi([AllValidatorStats([ValidatorStat(blocks=U32(0), tickets=U32(0), pre_images=U32(0), pre_images_size=U32(0), guarantees=U32(0), assurances=U32(0)) for _ in range(VALIDATOR_COUNT)]) for _ in range(2)]),
            nu=Nu([AllReadyWRs([]) for _ in range(EPOCH_LENGTH)]),
            xi=Xi([WorkDependencies([]) for _ in range(EPOCH_LENGTH)]),
        )
    
    def save(self, db: KVStore):
        data = self.transform()
        # Save the regular state data
        for key, value in data.items():
            db.put(bytes(key), bytes(value))
    
    @staticmethod
    def load(db: KVStore, keys: list[ByteArray32] = None) -> "State":
        data = {}
        service_ids:set[ServiceId]=set()

        if keys is None:
            for key, value in db.get_all().items():
                data[key] = Bytes(value)
        else:
            for i in range(1,16):
                state_key=construct_state_key(i)
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
                service_key=construct_state_key((255,service_id))
                data[service_key]=Bytes(db.get(bytes(service_key)))

        state = State.detransform(data)

        return state



