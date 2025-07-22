from time import time
from types import NoneType
from typing import TYPE_CHECKING, Optional
from py_ark_vrf import public_from_le_secret, secret_from_seed
from typing import Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tsrkit_types import U32, Bytes, Bytes32, Uint
from jam.types.protocol.core import CoreIndex
from jam.types.protocol.crypto import BlsPublic, Ed25519Public, Hash, OpaqueHash
from jam.types.protocol.validators import IPAddress, ValidatorData, ValidatorMetadata
from rockstore import RockStore
import random
from py_ark_vrf import public_from_le_secret

from jam.types.work.shard import ShardIndex
from jam.utils.constants import EPOCH_LENGTH, VALIDATOR_COUNT
from jam.utils.merkle.binary_merkle import OpaqueHashes

if TYPE_CHECKING:
    from jam.state.state import State 

class Settings:
    # Node settings
    NODE_NAME: str = "JAM-Node"
    NODE_ID: int | None = None

    # Env config
    ENV_PREFIX = "JAM_"
    ENV_FILE = "40000.env"

    # Database settings - can be null if data_path is not set up
    _main_db: RockStore | None
    _state_db: RockStore | None
    _audit_db: RockStore | None
    _d3l: RockStore | None

    _data_path: str

    # Key Store
    seed: Bytes32

    ed25519_public: Bytes32
    ed25519_private: Bytes32

    bandersnatch_public: Bytes32
    bandersnatch_private: Bytes32

    # Epoch-related
    _last_recorded_epoch = -1
    _validator_index: int | None
    _val: ValidatorData | None 

    def __init__(
        self,
        data_path: Optional[str],
        seed=Optional[int],
        name: str = "god_mode",
        port: int = 3000,
    ):
        self.NODE_NAME = name
        random.seed(port)
        self.NODE_ID = random.randint(0, 2**16 - 1)

        # Cleanup
        self.clear()

        self._main_db = None
        self._audit_db = None
        self._d3l = None
        self._state_db = None

        if data_path:
            import os

            data_path = data_path + str(port)
            # Create a folder for this node
            os.makedirs(data_path, exist_ok=True)
            # Setup DB
            self._main_db = RockStore(data_path + "/main")
            self._audit_db = RockStore(data_path + "/audit")
            self._d3l = RockStore(data_path + "/d3l")
            self._state_db = RockStore(data_path + "/state")
            self._data_path = data_path

        if seed is not None:
            self._seed = seed
            self.seed = Bytes32(b"".join([U32(seed).encode()] * 8))
            self.ed25519_private = Bytes32(Hash.blake2b(Bytes(b"jam_val_key_ed25519") + self.seed))
            self.ed25519_public = Bytes32(
                Ed25519PrivateKey.from_private_bytes(self.ed25519_private)
                .public_key()
                .public_bytes_raw()
            )
            self.bandersnatch_private = Bytes32(Hash.blake2b(Bytes(b"jam_val_key_bandersnatch") + self.seed))
            self.bandersnatch_public = Bytes32(secret_from_seed(self.bandersnatch_private)[0])


    def update(self, state: Optional["State"] = None):
        """
        Updates epoch related data
        TBD: Can be trigger via state transitions or keep checking while 
        """
        if not state:
            from jam.state.state import state

        curr_epoch = int(time() // 6 // EPOCH_LENGTH)

        if self._last_recorded_epoch == curr_epoch: 
            return
        
        for i, val in enumerate(state.kappa):
            if val.ed25519 == self.ed25519_public: # and val.bandersnatch == self.bandersnatch:
                self._validator_index = i
                self._val = val 
                break
        else:
            self._validator_index = None
            self._val = None

        self._last_recorded_epoch = curr_epoch 

    @property
    def main_db(self) -> RockStore:
        if not self._main_db:
            raise ValueError("DB Paths are not set, call configure_db_paths before this.")
        return self._main_db

    @property
    def audit_da(self) -> RockStore:
        if not self._audit_db:
            raise ValueError("DB Paths are not set, call configure_db_paths before this.")
        return self._audit_db

    @property
    def d3l(self) -> RockStore:
        if not self._d3l:
            raise ValueError("DB Paths are not set, call configure_db_paths before this.")
        return self._d3l

    @property
    def state_db(self) -> RockStore:
        if not self._state_db:
            raise ValueError("DB Paths are not set, call configure_db_paths before this.")
        return self._state_db

    def clear(self):
        if hasattr(self, "_main_db") and self._main_db:
            self._main_db.close()
            print("Closing main db")
        if hasattr(self, "_d3l") and self._d3l:
            self._d3l.close()
            print("Closing d3l db")
        if hasattr(self, "_audit_db") and self._audit_db:
            self._audit_db.close()
            print("Closing audits db")
        if hasattr(self, "_state_db") and self._state_db:
            self._state_db.close()
            print("Closing state db")

    @property
    def val(self) -> ValidatorData:
        if time()//(6)//EPOCH_LENGTH != self._last_recorded_epoch:
            raise ValueError("Validator data is not updated, call update() first.")
        if self._val is None:
            raise ValueError("Validator data is not set, check if the node is registered in the state.")
        return self._val

    @property
    def validator_index(self):
        if time()//(6)//EPOCH_LENGTH != self._last_recorded_epoch:
            raise ValueError("Validator index is not updated, call update() first.")
        if isinstance(self._validator_index, NoneType):
            raise ValueError("Validator index is not set, check if the node is registered in the state.")
        return self._validator_index 

    def get_shard_index(self, core_index: CoreIndex):
        from jam.utils.chainspec import chain_config

        vi = self.validator_index
        shard_index = ShardIndex(
            (core_index * chain_config.recovery_threshold + vi) % VALIDATOR_COUNT
        )

        return shard_index



# Default setting, to be easier to differentiate
settings: Settings = Settings(data_path=None, seed=None)


# When starting a node, pass node params to set global settings
def setup_setting(*args, **kwargs) -> Settings:
    global settings
    settings = Settings(*args, **kwargs)
    return settings
