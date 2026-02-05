import os

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from dot_ring import secret_from_seed

from jam.state.ghost import GhostState
from jam.types import Hash
from jam.types.state.eta import Eta
from jam.state.state import State
from tsrkit_types import U32, Bytes, U16
from jam.block import Block
from jam.types.state.kappa import Kappa
from jam.types.state.gamma import GammaP, GammaA, GammaS, GammaZ
from jam.types.state.psi import PsiO
from jam.types.state.iota import Iota
from jam.types.state.lambda_ import Lambda_
from jam.block import TicketsExtrinsic
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata, IPAddress
from jam.utils.dummy.dummy_state import create_dummy_state


def deepcopy(state: GhostState):
    return GhostState.from_json(state.to_json())



def create_block(slot: U32, tickets: list) -> Block:
    """Create a dummy block with specified parameters"""
    # Create a simple header
    block = Block.from_random()
    block.extrinsic.tickets = TicketsExtrinsic(tickets)
    block.header.slot = slot
    return block


def create_state(
    tau: U32,
    eta: Eta,
    lambda_: Lambda_,
    kappa: Kappa,
    gamma_p: GammaP,
    iota: Iota,
    gamma_a: GammaA,
    gamma_s: GammaS,
    gamma_z: GammaZ,
    offenders: PsiO,
) -> State:
    """Create a dummy state with specified components"""
    state = create_dummy_state()
    state.tau = tau
    state.eta = eta
    state.lambda_ = lambda_
    state.kappa = kappa
    state.gamma.p = gamma_p
    state.iota = iota
    state.gamma.a = gamma_a
    state.gamma.s = gamma_s
    state.gamma.z = gamma_z
    state.psi.offenders = offenders

    return state


def create_validator_data_from_keys():
    """Convert validator fixture data to ValidatorData objects"""
    return [build_validator_data(i) for i in range(6)]

def build_validator_data(seed: int) -> ValidatorData:
    meta = ValidatorMetadata(
        name=Bytes[10](os.urandom(10)),
        protocol=U16(seed),
        host=IPAddress.from_str("127.0.0.1"),
        port=U16(19800+seed),
        buffer=Bytes[110](110)
    )

    seed = Bytes[32](b"".join([U32(seed).encode()] * 8))
    ed25519_private = Bytes[32](Hash.blake2b(Bytes(b"jam_val_key_ed25519") + seed))
    ed25519_public = Bytes[32](
        Ed25519PrivateKey.from_private_bytes(ed25519_private)
        .public_key()
        .public_bytes_raw()
    )
    bandersnatch_seed = Bytes[32](Hash.blake2b(Bytes(b"jam_val_key_bandersnatch") + seed))
    pub, ss = secret_from_seed(bandersnatch_seed)
    bandersnatch_public = Bytes[32](pub)

    bls = Bytes[144](144)

    data = ValidatorData(
        bandersnatch_public,
        ed25519_public,
        bls,
        meta
    )

    return data