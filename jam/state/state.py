from typing import Type

from jam.config.data_stores import main_db
from jam.storage.db.kv import KVStore
from jam.state.accounts import DeltaView
from jam.state.ghost import GhostState
from jam.state.merkle import StateTrie
from jam.state.utils.key_constructor import construct_state_key
from jam.types.base import Bytes, ByteArray32
from jam.types.block import Block
from jam.types.state.alpha import Alpha, AuthorizationPool
from jam.types.state.eta import Eta
from jam.types.state.nu import Nu
from jam.types.state.pi import AllValidatorStats, Pi, ValidatorStat, AllServiceStats, AllCoreStats, CoreStat
from jam.types.state.psi import Psi, PsiB, PsiG, PsiO, PsiW
from jam.types.state.kappa import Kappa
from jam.types.state.lambda_ import Lambda_
from jam.types.state.rho import Rho
# from jam.types.state.rho import OptionalWorkReportState, Rho
from jam.types.state.tau import Tau
from jam.types.state.chi import Chi, ChiG
from jam.types.state.iota import Iota
# from jam.types.state.nu import AllReadyWRs, Nu
from jam.types.state.xi import Xi
from jam.types.state.delta import Delta
from jam.types.state.beta import Beta
from jam.types.state.phi import AuthorizationQueue, AuthorizerHash, Phi
from jam.types.state.gamma import Gamma, GammaA, GammaK, GammaZ, GammaS
from jam.types.state.delta import Delta, Ai, Ai, At, AccountData, AccountLookup, LookupTable, Timestamps, AccountPreimages, AccountStorage
from jam.utils.codec import Codable

def make_state_prop(state_key: int, cl: Type[Codable]):
    def fget(self):
        raw = self.DB.get(bytes(construct_state_key(state_key)))
        if raw is None:
            raise ValueError(f"State component missing from DB: {cl.__name__}")
        return cl.decode_from(raw)[0]

    def fset(self, value):
        k, v = construct_state_key(state_key), value.encode()
        self.TRIE.update(k, Bytes(v))
        self.DB.put(bytes(k), v)

    return property(fget, fset)

class State:
    """
    State implementation that uses dynamic components fetched from Db
    Here we retain and update merkle trie as cache
    """
    DB: KVStore
    TRIE: StateTrie

    alpha = make_state_prop(1, Alpha)
    phi = make_state_prop(2, Phi)
    beta = make_state_prop(3, Beta)
    gamma = make_state_prop(4, Gamma)
    psi = make_state_prop(5, Psi)
    eta = make_state_prop(6, Eta)
    iota = make_state_prop(7, Iota)
    kappa = make_state_prop(8, Kappa)
    lambda_ = make_state_prop(9, Lambda_)
    rho = make_state_prop(10, Rho)
    tau = make_state_prop(11, Tau)
    chi = make_state_prop(12, Chi)
    pi = make_state_prop(13, Pi)
    nu = make_state_prop(14, Nu)
    xi = make_state_prop(15, Xi)

    @property
    def delta(self) -> "DeltaView":
        return DeltaView(self.DB, self.TRIE)

    def __init__(self, db, trie):
        self.DB = db
        self.TRIE = trie

    @property
    def root(self):
        return self.TRIE.root_hash

    def transition(self, block: Block):
        """
        Main state transition function. Takes in the current state and the incoming block, returns the transitioned state

        Args:
            block: Incoming block
        """
        from jam.accumulation.accumulation import Accumulation
        from jam.report.state import Reporting
        from jam.authorization.authorization import Authorization
        from jam.recent_history.recent_history import RecentHistory
        from jam.consensus.safrole.safrole import Safrole
        from jam.assurances.assurances import Assurances
        from jam.disputes.disputes import Disputes
        from jam.preimages.preimages import Preimages
        from jam.statistics.statistics import Statistics

        # TODO: Validate block headers
        # Epoch markers - make sure eta0_1 are the same as current etas
        # Tickets mark - make sure tickets are valid, present in gamma_a and outside in sequenced
        # Offenders mark - make sure offenders are present in psi.offenders

        # 2. Disputes
        Disputes.transition(self, block)
        # 3. Assurances
        Assurances.transition(self, block)
        # 4. Reporting
        Reporting.transition(self, block)
        # 5. Accumulation
        _, beefy_map, acc_stats, _ = Accumulation.transition(self, block)
        # 6. Authorization
        Authorization.transition(self, block)
        # 7. Recent History  TODO: Calculate the accumulate root(r) from the commitment result from Accumulation.transition function()
        RecentHistory.transition(self, block, ByteArray32([0] * 32))
        # 8. Preimages
        Preimages.transition(self, block)
        # 9. Statistics
        Statistics.transition(self, block, [], {}, {})
        # 1. Safrole
        # Needs to be done after accumulation+statistics, as it requires Tau
        Safrole.transition(self, block, Safrole.vrf_output(block.header.entropy_source))

state = State(db=main_db, trie=StateTrie())

def setup_state(ghost: GhostState, db: KVStore):
    data = ghost.transform()
    trie = StateTrie()
    trie.merkelize(data, db)

    new_state = State(db, trie)
    global state
    state = new_state
    return state
