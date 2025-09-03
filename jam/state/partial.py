from copy import deepcopy
from tsrkit_types import structure
from jam.state.accounts import DeltaView
from jam.state.utils import make_state_prop
from jam.state.storage import StateStorage
from jam.types.state.chi import Chi
from jam.types.state.delta import Delta
from jam.types.state.iota import Iota
from jam.types.state.phi import Phi


class PartialState:
    authorizer_keys       = make_state_prop(2,  Phi)
    validator_keys        = make_state_prop(7,  Iota)
    privileges            = make_state_prop(12,  Chi)

    @property
    def service_accounts(self) -> "DeltaView":
        return DeltaView(self.store)
    
    def __init__(self, _store: StateStorage):
        self.store = _store
        
    def clone(self, copy_cache = False) -> "PartialState":
        return PartialState(
            StateStorage(
                self.store._TRIE, 
                self.store._DB, 
                {} if not copy_cache else self.store._CACHE.copy(),
                True
            )
        )


@structure
class GhostPartial:
    # d
    service_accounts: Delta
    # i
    validator_keys: Iota
    # q
    authorizer_keys: Phi
    # m, a, v, z
    privileges: Chi

    def clone(self) -> "GhostPartial":
        return deepcopy(self)