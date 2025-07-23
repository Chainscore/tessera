from typing import Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from tsrkit_types import U32, Bytes, Uint
from jam.types.protocol.crypto import BlsPublic, Hash
from jam.types.protocol.validators import IPAddress, ValidatorData, ValidatorMetadata
from rockstore import RockStore
import random
import py_ark_vrf as vrf


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
    seed: Bytes[32]
    ed25519_private: Bytes[32]
    bandersnatch_private: Bytes[32]

    @property
    def bandersnatch_public(self) -> Bytes[32]:
        if not self.bandersnatch_private:
            raise ValueError("Keys not set")
        secret_key = vrf.SecretKey(self.bandersnatch_private)
        return Bytes[32](secret_key.public().to_bytes())

    @property
    def ed25519_public(self) -> Bytes[32]:
        if not self.ed25519_private:
            raise ValueError("Keys not set")
        ed25519_public: Ed25519PublicKey = Ed25519PrivateKey.from_private_bytes(
            self.ed25519_private
        ).public_key()
        return Bytes[32](ed25519_public.public_bytes_raw())

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
            self.seed = Bytes[32](b"".join([U32(seed).encode()] * 8))
            self.ed25519_private = Hash.blake2b(
                Bytes(b"jam_val_key_ed25519") + self.seed
            )
            self.bandersnatch_private = Hash.blake2b(
                Bytes(b"jam_val_key_bandersnatch") + self.seed
            )

    @property
    def main_db(self) -> RockStore:
        if not self._main_db:
            raise ValueError(
                "DB Paths are not set, call configure_db_paths before this."
            )
        return self._main_db

    @property
    def audit_da(self) -> RockStore:
        if not self._audit_db:
            raise ValueError(
                "DB Paths are not set, call configure_db_paths before this."
            )
        return self._audit_db

    @property
    def d3l(self) -> RockStore:
        if not self._d3l:
            raise ValueError(
                "DB Paths are not set, call configure_db_paths before this."
            )
        return self._d3l

    @property
    def state_db(self) -> RockStore:
        if not self._state_db:
            raise ValueError(
                "DB Paths are not set, call configure_db_paths before this."
            )
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
        return ValidatorData(
            bandersnatch=self.bandersnatch_public,
            ed25519=self.ed25519_public,
            bls=BlsPublic(144),
            metadata=ValidatorMetadata(
                name=Bytes[10](b"alice"),
                protocol=Uint[16](0),
                host=IPAddress.from_json([0, 0, 0, 0]),
                port=Uint[16](40000),
                buffer=Bytes[110](110),
            ),
        )


# Default setting, to be easier to differentiate
settings: Settings = Settings(data_path=None, seed=None)


# When starting a node, pass node params to set global settings
def setup_setting(*args, **kwargs) -> Settings:
    global settings
    settings = Settings(*args, **kwargs)
    return settings
