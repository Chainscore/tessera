"""Root conftest — shared fixtures for all tests.

The main fixture is `jam_node` which yields a fully initialized JamNode.
Tests access node.state, node.settings, node.grandpa, etc. directly.
Just like the old setup_setting/setup_state pattern but scoped to a node instance.
"""
import json
import pytest
from pathlib import Path

DEV_SPEC = Path(__file__).parent.parent / "dev-spec.json"


def _init_node(tmp_path, seed=0, rpc=False, port=40000, rpc_port=19800):
    """Create and initialize a JamNode without entering the TaskGroup.

    Mirrors JamNode.start() init sequence:
    - setup settings (RocksDB in tmp_path)
    - create services (rpc, ledger, grandpa, router, operator)
    - hydrate state from dev-spec.json
    - save + finalize genesis block
    """
    from jam.config import NodeConfig
    from jam.jam_node import JamNode
    from jam.settings import Settings
    from jam.state.state import setup_state
    from jam.block.block import Block
    from jam.api.rpc.service import RPCService
    from jam.block.block_view import BlockView
    from jam.finality.service import FinalityService
    from jam.network.service import NetworkService
    from jam.operations.service import OperatorService

    config = NodeConfig(
        PORT=port,
        RPC_PORT=rpc_port,
        SEED=str(seed),
        DATA_PATH=str(tmp_path) + "/",
        RPC_FLAG=rpc,
        LOG_LEVEL="WARNING",
    )

    node = JamNode(config)

    # Init services (mirrors JamNode.start lines 264-281)
    node._settings = Settings(config)
    node._responder = RPCService(node)
    node._ledger = BlockView(node)
    node._grandpa = FinalityService(node)
    node._router = NetworkService(node)
    node._operator = OperatorService(node)

    # State from dev-spec.json
    node.state = setup_state(node, genesis="dev-spec.json")
    node.state.store.enable_writes()
    node.state.store.enable_cache()

    # Genesis block
    spec = json.loads(DEV_SPEC.read_text())
    block = Block.decode(bytes.fromhex(spec["genesis_header"]))
    block.save(node.settings.main_db)
    node.grandpa.set_head(block)
    node.grandpa.finalise(block, initial=True)

    return node


# ─── Fixtures ───

@pytest.fixture
def db_path(tmp_path):
    """Temporary directory for raw RocksDB tests."""
    yield str(tmp_path)


@pytest.fixture
async def jam_node(tmp_path):
    """Fully initialized JamNode — state, settings, services, genesis finalized.

    Access node.state, node.settings, node.grandpa, node.operator, etc.
    No services are *running* (no network loop, no operator loop, no RPC server).
    Async because BlockView.record_block needs an event loop.
    """
    node = _init_node(tmp_path)
    try:
        yield node
    finally:
        node.settings.clear()


@pytest.fixture
async def jam_node_rpc(tmp_path):
    """JamNode with RPC flag on — for tests that need rpc test client."""
    node = _init_node(tmp_path, rpc=True, rpc_port=19800)
    try:
        yield node
    finally:
        node.settings.clear()


def pytest_addoption(parser):
    parser.addoption(
        "--no-rpc",
        action="store_false",
        default=True,
        help="Flag for turning rpc off"
    )


@pytest.fixture
def rpc(request):
    return request.config.getoption("--no-rpc")
