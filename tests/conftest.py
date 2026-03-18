"""Root conftest — all test fixtures.

Unit:
  jam_node      — stopped node, services wired but not running
  jam_node_rpc  — stopped node with RPC enabled
  db_path       — temp directory for raw RocksDB tests
"""
import json
import pytest
from pathlib import Path

DEV_SPEC = Path(__file__).parent.parent / "dev-spec.json"


def _init_node(tmp_path, seed=0, rpc=False, port=40000, rpc_port=19800):
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
    node._settings = Settings(config)
    node._responder = RPCService(node)
    node._ledger = BlockView(node)
    node._grandpa = FinalityService(node)
    node._ledger.initialize()

    node._router = NetworkService(node)
    node._operator = OperatorService(node)

    node.state = setup_state(node, genesis="dev-spec.json")
    node.state.store.enable_writes()
    node.state.store.enable_cache()

    spec = json.loads(DEV_SPEC.read_text())
    block = Block.decode(bytes.fromhex(spec["genesis_header"]))
    block.save(node.settings.main_db)
    node.grandpa.set_head(block)
    node.grandpa.finalise(block, initial=True)

    return node


@pytest.fixture
def db_path(tmp_path):
    yield str(tmp_path)


@pytest.fixture
async def jam_node(tmp_path):
    node = _init_node(tmp_path)
    try:
        yield node
    finally:
        node.settings.clear()


@pytest.fixture
async def jam_node_rpc(tmp_path):
    node = _init_node(tmp_path, rpc=True, rpc_port=19800)
    try:
        yield node
    finally:
        node.settings.clear()


def pytest_addoption(parser):
    parser.addoption("--no-rpc", action="store_false", default=True, help="Turn rpc off")


@pytest.fixture
def rpc(request):
    return request.config.getoption("--no-rpc")
