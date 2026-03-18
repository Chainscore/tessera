from copy import deepcopy
from typing import TYPE_CHECKING

from tsrkit_types import structure
from jam.state.accounts import DeltaView
from jam.state.utils import make_state_prop
from jam.state.storage import StateStorage
from jam.types.state.chi import Chi
from jam.types.state.delta import Delta
from jam.types.state.iota import Iota
from jam.types.state.phi import Phi

if TYPE_CHECKING:
    from jam.jam_node import JamNode


class PartialState:
    authorizer_keys       = make_state_prop(2,  Phi)
    validator_keys        = make_state_prop(7,  Iota)
    privileges: Chi       = make_state_prop(12,  Chi)

    @property
    def service_accounts(self) -> "DeltaView":
        return DeltaView(self.store, self.jam)
    
    def __init__(self, _jam: "JamNode", _store: StateStorage):
        self.store = _store
        self.jam = _jam
        
    def clone(self, copy_cache = False, reset_inherited = True) -> "PartialState":
        # When copying cache, track which keys were inherited so merge can filter them out
        if copy_cache:
            inherited = set(self.store._updates.keys()) if reset_inherited else self.store._inherited_keys.copy()
        else:
            inherited = set()
        return PartialState(
            self.jam,
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