from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from ..storage.state_keys import construct_state_key, STATE_KEY_PREFIXES
from .components import Alpha, Beta

@dataclass
class State:
    alpha: Alpha
    beta: Beta
    