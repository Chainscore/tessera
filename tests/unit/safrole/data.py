from jam.consensus.safrole.safrole import Safrole
from jam.types.state.eta import Eta
from jam.state.state import State
from tsrkit_types.integers import U32
from jam.types.block import Block
from jam.types.state.kappa import Kappa
from jam.types.state.gamma import GammaK, GammaA, GammaS, GammaZ
from jam.types.state.psi import PsiO
from jam.types.state.iota import Iota
from jam.types.state.lambda_ import Lambda_
from jam.types.extrinsics import (
    TicketsExtrinsic,
)
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic, Ed25519Public
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata
from jam.utils.dummy.dummy_state import create_dummy_state

def validators():
    return [
        {
            "seed": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "ed25519_private": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "ed25519_public": "0x3b6a27bcceb6a42d62a3a8d02a6f0d73653215771de243a63ac048a18b59da29",
            "bandersnatch_private": "0x51c1537c18eea5c5969cb2ae45c1224cc245de5c5b8e6e25f48fb99f2786ee05",
            "bandersnatch_public": "0x5e465beb01dbafe160ce8216047f2155dd0569f058afd52dcea601025a8d161d",
            "dns_alt_name": "ehnvcppgow2sc2yvdvdicu3ynonsteflxdxrehjr2ybekdc2z3iuq"
        },
        {
            "seed": "0x0100000001000000010000000100000001000000010000000100000001000000",
            "ed25519_private": "0x0100000001000000010000000100000001000000010000000100000001000000",
            "ed25519_public": "0x22351e22105a19aabb42589162ad7f1ea0df1c25cebf0e4a9fcd261301274862",
            "bandersnatch_private": "0x9e84e7bb7c172ba7c0549f495b2412ce7d9d862719d5de4db97bacd97b60b505",
            "bandersnatch_public": "0x3d5e5a51aab2b048f8686ecd79712a80e3265a114cc73f14bdb2a59233fb66d0",
            "dns_alt_name": "eei2r4iqqlim2vo2clciwfll7d2qn6hbfz27q4su7zutbgajhjbra"
        },
        {
            "seed": "0x0200000002000000020000000200000002000000020000000200000002000000",
            "ed25519_private": "0x0200000002000000020000000200000002000000020000000200000002000000",
            "ed25519_public": "0xe68e0cf7f26c59f963b5846202d2327cc8bc0c4eff8cb9abd4012f9a71decf00",
            "bandersnatch_private": "0x91ebd09c591e41858a7a2a45c671642708f546c163b76eef0991b755017e7412",
            "bandersnatch_public": "0xaa2b95f7572875b0d0f186552ae745ba8222fc0b5bd456554bfe51c68938f8bc",
            "dns_alt_name": "e42haz57snrm7sy5vqrrafursptelydco76gltk6uaexzu4o6z4aa"
        },
        {
            "seed": "0x0300000003000000030000000300000003000000030000000300000003000000",
            "ed25519_private": "0x0300000003000000030000000300000003000000030000000300000003000000",
            "ed25519_public": "0xb3e0e096b02e2ec98a3441410aeddd78c95e27a0da6f411a09c631c0f2bea6e9",
            "bandersnatch_private": "0x40ad858dd0abe3016f7834831c93ae02764e0bb99ee204ffc6777b01c946ac0c",
            "bandersnatch_public": "0x7f6190116d118d643a98878e294ccf62b509e214299931aad8ff9764181a4e33",
            "dns_alt_name": "ewpqobfvqfyxmtcruifaqv3o5pdev4j5a3jxucgqjyyy4b4v6u3uq"
        },
        {
            "seed": "0x0400000004000000040000000400000004000000040000000400000004000000",
            "ed25519_private": "0x0400000004000000040000000400000004000000040000000400000004000000",
            "ed25519_public": "0x5c7f34a4bd4f2d04076a8c6f9060a0c8d2c6bdd082ceb3eda7df381cb260faff",
            "bandersnatch_private": "0x0dea7844b6b937f8b00acea90a8ce9dfe07fdbd2a1e4ff09022340d9bb159911",
            "bandersnatch_public": "0x48e5fcdce10e0b64ec4eebd0d9211c7bac2f27ce54bca6f7776ff6fee86ab3e3",
            "dns_alt_name": "elr7tjjf5j4wqib3krrxzayfazdjmnpoqqlhlh3nh344bzmta7l7q"
        },
        {
            "seed": "0x0500000005000000050000000500000005000000050000000500000005000000",
            "ed25519_private": "0x0500000005000000050000000500000005000000050000000500000005000000",
            "ed25519_public": "0x837ce344bc9defceb0d7de7e9e9925096768b7adb4dad932e532eb6551e0ea02",
            "bandersnatch_private": "0x68f5494ec1c3d3cd8ff2a3cb285abf0e826b2c762d95fc2e953eaef666315403",
            "bandersnatch_public": "0xf16e5352840afb47e206b5c89f560f2611835855cf2e6ebad1acc9520a72591d",
            "dns_alt_name": "eqn6ogrf4txx45mgx3z7j5gjfbftwrn5nwtnnsmxfglvwkupa5iba"
        }
    ]

def generate_ticket():
    """Generate a test ticket envelope"""
    return Safrole.generate_ticket()

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
    return [
        ValidatorData(
            bandersnatch=BandersnatchPublic(v["bandersnatch_public"]),
            ed25519=Ed25519Public(v["ed25519_public"]),
            bls=BlsPublic(bytes(144)),  # Dummy BLS key
            metadata=ValidatorMetadata.from_json({"name": "test", "host": [0,0,0,0], "port": 1000})  # Dummy metadata
        )
        for v in validators()
    ]
