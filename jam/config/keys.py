from tsrkit_types import Bytes, U32
from jam.types import Hash
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
import py_ark_vrf as vrf

class KeysConfig:
	ed25519_private: Bytes[32]
	bandersnatch_private: Bytes[32]

	@classmethod
	def from_seed(cls, seed: int):
		ret = cls()
		trivial_seed = b"".join([U32(seed).encode()] * 8)
		ret.ed25519_private = Hash.blake2b(Bytes(b"jam_val_key_ed25519") + trivial_seed)
		ret.bandersnatch_private = Hash.blake2b(Bytes(b"jam_val_key_bandersnatch") + trivial_seed)
		return ret

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


keys = KeysConfig()

def setup_keys(seed: int):
	global keys
	keys = KeysConfig.from_seed(seed)
	return keys