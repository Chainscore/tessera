from typing import Type

from jam.config.data_stores import main_db
from jam.db.kv import KVStore
from jam.state.accounts import DeltaView
from jam.state.ghost import GhostState
from jam.state.merkle import StateTrie
from jam.types import Bytes
from jam.state.utils.key_constructor import construct_state_key
from jam.types.state import Alpha, Beta, Phi, Eta, Tau, Gamma, Psi, Pi, Nu, Xi, Chi, Rho, Lambda_, Kappa, Iota
from jam.utils.codec import Codable

def make_state_prop(state_key: int, cl: Type[Codable]):
    def fget(self):
        raw = self.DB.get(bytes(construct_state_key(state_key)))
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

state = State(db=main_db, trie=StateTrie())

def setup_state(ghost: GhostState, db: KVStore):
    data = ghost.transform()
    for key, value in data.items():
        db.put(bytes(key), bytes(value))
    trie = StateTrie()
    trie.merkelize(data)

    new_state = State(db, trie)
    global state
    state = new_state
