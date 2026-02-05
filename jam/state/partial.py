from copy import deepcopy
from tsrkit_types import structure
from jam.state.accounts import DeltaView
from jam.state.utils import make_state_prop
from jam.state.storage import StateStorage
from jam.models.state.chi import Chi
from jam.models.state.delta import Delta
from jam.models.state.iota import Iota
from jam.models.state.phi import Phi


class PartialState:
    authorizer_keys       = make_state_prop(2,  Phi)
    validator_keys        = make_state_prop(7,  Iota)
    privileges: Chi            = make_state_prop(12,  Chi)

    @property
    def service_accounts(self) -> "DeltaView":
        return DeltaView(self.store)
    
    def __init__(self, _store: StateStorage):
        self.store = _store
        
    def clone(self, copy_cache = False, reset_inherited = True) -> "PartialState":
        # When copying cache, track which keys were inherited so merge can filter them out
        if copy_cache:
            inherited = set(self.store._updates.keys()) if reset_inherited else self.store._inherited_keys.copy()
        else:
            inherited = set()
        return PartialState(
            StateStorage(
                self.store._TRIE, 
                self.store._DB, 
                {} if not copy_cache else self.store._updates.copy(),
                True,
                inherited_keys=inherited
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
    # m, a, v, r, z
    privileges: Chi

    def clone(self) -> "GhostPartial":
        return deepcopy(self)