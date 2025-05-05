from jam.db.kv import KVStore
from jam.state.components.alpha import Alpha, AuthorizationPool
from jam.state.components.eta import Eta
from jam.state.components.pi import AllValidatorStats, Pi, ValidatorStat, AllServiceStats, AllCoreStats, CoreStat
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
from jam.types.block import Block
from jam.types.base.integers.fixed import U64, U32, U8, U16
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
from jam.types.protocol.validators import IPAddress, ValidatorData, ValidatorMetadata, ValidatorName, ValidatorsData
from jam.types.work.report import WorkDependencies
from jam.utils.constants import CORE_COUNT, EPOCH_LENGTH, MAX_AUTH_QUEUE_ITEMS, VALIDATOR_COUNT
from jam.accumulation.accumulation import Accumulation
from jam.report.state import Reporting
from jam.authorization.authorization import Authorization
from jam.recent_history.recent_history import RecentHistory
from jam.consensus.safrole.safrole import Safrole
from jam.assurances.assurances import Assurances
from jam.disputes.disputes import Disputes
from jam.preimages.preimages import Preimages
from jam.statistics.statistics import Statistics
import json


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

    @staticmethod
    def from_random(seed = 0) -> "State":
        from tests.dummy.dummy_state_comp import create_dummy_state_components

        return State(**create_dummy_state_components())

    def transform(self) -> dict:
        """
            Transform the state into a dictionary as defined in D.2
            Returns:
                dict: A dictionary representation of the state in this format: {bytes -> Bytes}
        """
        services, service_storage, service_preimages, service_lookup = self.delta.transform()
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
            delta=Delta.detransform(state),
        )

    def generate_root(self) -> ByteArray32:
        """Generate the root hash of the state"""
        return self._merkle.merkelize(self.transform())[0]

    def get_merkle_nodes(self) -> dict:
        """Get all nodes in the state Merkle trie"""
        return self._merkle.get_nodes()
    
    @staticmethod
    def genesis(genesis_path = "genesis.json") -> "State":
        """Generate the genesis state"""
        peers = ValidatorsData.from_json(json.load(open(genesis_path))["peers"])
        empty_set = [ValidatorData(
            bandersnatch=BandersnatchPublic(bytes(32)),
            ed25519=Ed25519Public(bytes(32)),
            bls=BlsPublic(bytes(144)),
            metadata=ValidatorMetadata(ValidatorName(""), IPAddress([U8(127), U8(0), U8(0), U8(1)]), U16(0))
        ) for _ in range(VALIDATOR_COUNT)]
        fallback = Safrole.arrange_fallback(ByteArray32(bytes(32)), peers)

        return State(
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
    
    def save(self, db:KVStore, updated_keys:list[ByteArray32,Bytes]=None):
        """
        Save state to the key-value store.
        
        If the root hash is not initialized (all zeros), merkelize the full state and save all key-value pairs.
        Otherwise, update only the modified paths, root hash, and state keys in the database.
        """
        data = self.transform()
        if self._merkle.trie._root_hash == ByteArray32([0] * 32):
            self._merkle.merkelize(data)
            # db.put(b"general_root:",bytes(general_root))
            for key, value in data.items():
                db.put(bytes(key), bytes(value))
        else:
            root=self._merkle.update_global_root(updated_keys)
            # db.put(b"general_root:",bytes(general_root))
            for key,value in updated_keys.items():
                db.put(bytes(key),bytes(value))

    @staticmethod
    def load(db: KVStore, keys: list[ByteArray32] = []) -> "State":
        data = {}
        service_ids:set[ServiceId]=set()

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

    def transition(self, block: Block) -> "State":
        """
        Main state transition function. Takes in the current state and the incoming block, returns the transitioned state

        Args:
            pre_state: Current state
            block: Incoming block

        Returns:
            State: The transitioned state
        """

        # TODO: Validate block headers
        # Epoch markers - make sure eta0_1 are the same as current etas
        # Tickets mark - make sure tickets are valid, present in gamma_a and outside in sequenced
        # Offenders mark - make sure offenders are present in psi.offenders

        # 1. Safrole
        entropy = ByteArray32(bytes(32))
        sigma = Safrole.transition(self, block, entropy)
        # 2. Disputes
        sigma = Disputes.transition(sigma, block)
        # 3. Assurances
        sigma = Assurances.transition(sigma, block)
        # 4. Reporting
        sigma = Reporting.transition(sigma, block)
        # 5. Accumulation
        sigma = Accumulation.transition(sigma, block)
        # 6. Authorization
        sigma = Authorization.transition(sigma, block)
        # 7. Recent History
        sigma = RecentHistory.transition(sigma, block, ByteArray32([0] * 32))
        # 8. Preimages
        sigma = Preimages.transition(sigma, block)
        # 9. Statistics
        sigma = Statistics.transition(sigma, block)

        return sigma
