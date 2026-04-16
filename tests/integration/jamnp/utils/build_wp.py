from jam.block import Block
from jam.finality.finality import Finality
from jam.models import RefineContext, BeefyRoot, HeaderHash, ServiceId
from jam.models.state.beta import BlockHistory
from jam.models.work import WorkItems
from jam.utils.dummy.dummy_package import create_dummy_package
from jam.utils.merkle import MMRFunctions

from tsrkit_types import Bytes

merklizer = MMRFunctions()


def get_context():
    from jam.state.state import state
    from jam.settings import settings

    if not len(state.beta):
        print("Block History not available!")
        return

    lookup_anchor: Block = Finality.load_final(settings.main_db)
    last_block: Block = Finality.load_latest(settings.main_db)
    anchor: BlockHistory = state.beta[-1]
    refine_context = RefineContext.empty()

    refine_context.anchor = anchor.header_hash
    refine_context.state_root = state.root
    refine_context.beefy_root = BeefyRoot(merklizer.super_peak(anchor.mmr))
    # refine_context.lookup_anchor = HeaderHash(lookup_anchor.header.hash())
    # refine_context.lookup_anchor_slot = lookup_anchor.header.slot

    refine_context.lookup_anchor = HeaderHash(last_block.header.hash())
    refine_context.lookup_anchor_slot = last_block.header.slot

    return refine_context


def build_package():
    from jam.state.state import state

    auth_code_host = ServiceId(0)
    auth_code_hash = state.delta[auth_code_host].service.code_hash

    wp = create_dummy_package()
    context = get_context()

    if not context:
        print("Couldn't override work package's context")
        return wp

    wp.context = context
    wp.auth_code_host = auth_code_host
    wp.authorizer.code_hash = auth_code_hash
    wp.authorizer.params = Bytes(b"")

    # TODO: Handle this according to custom services
    wp.items = WorkItems([])

    return wp