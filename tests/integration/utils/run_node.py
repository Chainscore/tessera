from pathlib import Path
import shutil
import json
import asyncio
import signal
import logging
import os
import time
from dotenv import load_dotenv

from jam.log_setup import setup_logging
from jam.utils.chainspec import chain_config
from .state_update import update_state

from jam.finality.finality import Finality
from jam.settings import setup_setting
from jam.network.start import start_node
from jam.state.state import setup_state
from jam.block import Block

from jam.log_setup import node_logger as logger
from jam.operations.ticket_queue import setup_ticket_queue
from jam.api.rpc.app import rpc


shutdown_event = asyncio.Event()

async def rpc_shutdown_trigger():
    await shutdown_event.wait()

async def run_node(
    db: str,
    env: str,
    theme: str,
    is_builder: bool,
    is_validator: bool,
    node_tasks,
    rpc_flag: bool
) -> None:

    # ---------- LOAD ENVIRONMENT ----------
    load_dotenv(".env")
    load_dotenv(env,override=True)

    name = os.environ.get("NODE_NAME", "jam-node")
    port = os.environ.get("PORT", 40000)
    seed = os.environ.get("SEED", "0")
    host = os.environ.get("HOST", "0.0.0.0")
    if rpc_flag:
        rpc_port = os.environ.get("RPC_PORT", 19800)
        rpc_host = os.environ.get("RPC_HOST", "0.0.0.0")

    if not name or not port or not host or not seed:
        raise ValueError(f"Missing node info in {env}")

    # ---------- SETUP LOGGING ----------
    setup_logging(theme=theme, node_name=name)

    # ---------- SETUP SETTINGS ----------
    settings = setup_setting(
        name=name, port=int(port), seed=int(seed), data_path=db, rpc_flag=rpc_flag
    )

    main_db = settings.main_db

    if rpc_flag:
        logger.info(f"Starting Tessera Node! name={name} port={port} spec={chain_config.name} rpc_port={rpc_port}")
    else:
        logger.info(f"Starting Tessera Node! name={name} port={port} spec={chain_config.name}")

    try:
        # -------------- SETUP STATE -------------
        # Set genesis state
        dev_spec = json.load(open("dev-spec.json"))
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
        state = setup_state(settings.state_db, "dev-spec.json")

        # FIX: setup ticket queue
        setup_ticket_queue()

        # ------------ SET GENESIS BLOCK ------------
        block = Block.decode(bytes.fromhex(dev_spec["genesis_header"]))
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)
        Finality.finalise(header_hash, main_db, True)

        # ----------- START NODE --------------
        async with asyncio.TaskGroup() as tg:
            # Networking - Block Imports, WP Processing, etc
            tg.create_task(start_node(str(host), int(port), is_builder))
            if rpc_flag:
                # RPC
                tg.create_task(rpc.run_task(debug=True, host=rpc_host, port=rpc_port, shutdown_trigger=rpc_shutdown_trigger))
            # Node Ops - Block Prod, Audit, Assurances, etc
            for node_task in node_tasks:
                if node_task:
                    tg.create_task(node_task())

    except Exception as e:
        shutdown_event.set()
        logger.critical("Fatal error", e=e, error_type=type(e).__name__)
        # Close db connections
        if Path("data/tmp").exists():
            shutil.rmtree("data/tmp")
        settings.clear()
        raise asyncio.exceptions.CancelledError
    finally:
        loop = asyncio.get_running_loop()
        for t in asyncio.all_tasks(loop):
            t.cancel()

def run_node_process(
        db: str,
        env: str,
        start_genesis: bool,
        theme: str,
        is_builder: bool,
        is_validator: bool,
        node_tasks,
        rpc_flag: bool
):
    try:
        # Handle clean termination
        def handle_sigterm(signum, frame):
            exit(0)

        signal.signal(signal.SIGTERM, handle_sigterm)

        asyncio.run(run_node(
            db,
            env,
            theme,
            is_builder,
            is_validator,
            node_tasks,
            rpc_flag
        ))
    except asyncio.exceptions.CancelledError:
        asyncio.Runner().close()
        print("\nCtrl-C received, Node shutting down!!!!!!")


