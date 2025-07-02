from contextlib import contextmanager
import os
import pytest
from jam.settings import Settings, setup_setting
from jam.network.base.certificate import generate_san
from jam.network.peer import Peer
from jam.network.node import Node
from dotenv import load_dotenv


@contextmanager
def using_node(db_path: str, port: int):
    load_dotenv(f"envs/{port}.env")
    
    setting = setup_setting(
        name=getattr(os.environ, "NODE_NAME", "god"),
        port=port,
        seed=getattr(os.environ, "SEED", 2**16 - 1),
        data_path=db_path
    )
    
    try:
        yield setting
    finally:
        setting.clear()


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async tests not enabled")
async def test_ce128_setup(db_path):
    """
    Here we'll setup a connection between two nodes, and
    both be having sperate block history
    """

    # Configure db_path
    # DataStores.configure_db_paths(db_path)

    a = Settings("alice", 40000, 0)
    b = Settings("bob"  , 40001, 1)
    
    a_peer = Peer(id=generate_san(a.ed25519_public), data=a.val)
    b_peer = Peer(id=generate_san(b.ed25519_public), data=b.val)

    # Start initialization
    os.environ["SEED"] = "0"

    alice = Node(
        "alice",
        "0.0.0.0",
        40000,
        a.val,
        peers=[b_peer],
        is_builder=False,
        is_validator=True,
    )
    with using_node(db_path, 40000) as s:
        a_server_task = alice.run_server()
        a_client_task = alice.run_client()

    os.environ["SEED"] = "1"

    bob = Node(
        "bob",
        "0.0.0.0",
        40001,
        b.val,
        peers=[a_peer],
        is_builder=False,
        is_validator=True,
    )

    b_server_task = bob.run_server()
    b_client_task = bob.run_client()

    # Start servers
    await a_server_task
    await b_server_task

    # Connect with peers
    await a_client_task
    await b_client_task
