from jam.settings import Settings
from jam.state.ghost import GhostState
from jam.state.transitions import Safrole
from jam.types.state.eta import Eta
from jam.state.state import State
from tsrkit_types.integers import U32
from jam.block import Block
from jam.types.state.kappa import Kappa
from jam.types.state.gamma import GammaK, GammaA, GammaS, GammaZ
from jam.types.state.psi import PsiO
from jam.types.state.iota import Iota
from jam.types.state.lambda_ import Lambda_
from jam.block import TicketsExtrinsic
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic, Ed25519Public
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata
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
    gamma_k: GammaK, 
    iota: Iota, 
    gamma_a: GammaA, 
    gamma_s: GammaS, 
    gamma_z: GammaZ, 
    offenders: PsiO
) -> State:
    """Create a dummy state with specified components"""
    state = create_dummy_state()
    state.tau = tau
    state.eta = eta
    state.lambda_ = lambda_
    state.kappa = kappa
    state.gamma.k = gamma_k
    state.iota = iota
    state.gamma.a = gamma_a
    state.gamma.s = gamma_s
    state.gamma.z = gamma_z
    state.psi.offenders = offenders
    
    return state

def create_validator_data_from_keys():
    """Convert validator fixture data to ValidatorData objects"""
    return [Settings(None, i).val for i in range(6)]
