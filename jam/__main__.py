import asyncio
import json
import logging
import os
from pathlib import Path
import shutil
from typing import TYPE_CHECKING
from dotenv import load_dotenv

from jam.telemetry.events import ServiceId
from jam.types import Hash, AccountData, LookupTable, BlobLength, Timestamps, TimeSlot
from jam.types.state.delta import ServiceCodeHash

if TYPE_CHECKING:
    from jam.finality.finality import Finality
    from jam.log_setup import setup_logging
    from jam.network.start import start_node
    from jam.operations.operator import operate
    from jam.utils.chainspec import chain_config
    from jam.settings import setup_setting
    from jam.state.state import setup_state
    from jam.block import Block
    from jam.api.rpc.app import rpc
    from jam.operations.ticket_queue import setup_ticket_queue
    from jam.telemetry.client import TelemetryClient, TelemetryConfig

from jam.log_setup import setup_logging, logger
from jam.network.start import start_node
from jam.operations.operator import operate
from jam.operations.ticket_queue import setup_ticket_queue
from jam.state.state import setup_state
from jam.settings import setup_setting
from jam.finality.finality import Finality
from jam.block import Block
from jam.api.rpc.app import rpc
from jam.utils.chainspec import chain_config
from jam.telemetry.client import TelemetryClient, TelemetryConfig

shutdown_event = asyncio.Event()

def handle_exception(loop, context):
    """Custom exception handler for the event loop."""
    msg = context.get("exception", context["message"])
    exception = context.get("exception")
    if exception:
        import traceback
        tb_str = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        logger.error(f"Unhandled event loop exception: {msg}\n{tb_str}")
    else:
        logger.error(f"Unhandled event loop error: {msg}")

async def rpc_shutdown_trigger():
    await shutdown_event.wait()

async def main(
    db: str,
    env: str,
    theme: str,
    is_builder: bool,
    is_validator: bool,
    rpc_flag: bool,
    telemetry: str|None
) -> None:
    if not is_builder and not is_validator:
        is_validator=True

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

    # ---------- SETUP TELEMETRY (optional) ----------
    telemetry_client = None
    if telemetry:
        telemetry_host, telemetry_port_str = telemetry.split(":")
        telemetry_port = int(telemetry_port_str)
        telemetry_config = TelemetryConfig(
            host=telemetry_host,
            port=telemetry_port,
            node_name=name
        )
        telemetry_client = TelemetryClient.setup(telemetry_config)
        logger.info(f"Telemetry enabled: {telemetry_host}:{telemetry_port}")

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
        # Set up custom exception handler for the event loop
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(handle_exception)
        
        # -------------- SETUP STATE -------------
        # Set genesis state
        dev_spec = json.load(open("dev-spec.json"))
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync

        # TODO: Remove this after testing
        state = setup_state(settings.state_db, "dev-spec.json")
        service_id = ServiceId(34)
        code = bytes("fjsghfajklsdhfjkalsf", 'utf-8')
        code_hash = Hash.blake2b(code)
        state.delta[service_id] = AccountData()
        state.delta[service_id].service.code_hash = code_hash
        state.delta[service_id].preimages[code_hash] = code
        lookup_key = LookupTable(hash=ServiceCodeHash(code_hash), length=BlobLength(len(code)))
        state.delta[service_id].lookup[lookup_key] = Timestamps([TimeSlot(0)])


        # FIX: setup ticket queue
        setup_ticket_queue()

        # ------------ SET GENESIS BLOCK ------------
        block = Block.decode(bytes.fromhex(dev_spec["genesis_header"]))
        header_hash = block.save(main_db)
        Finality.set_head(block, main_db)
        Finality.finalise(block, main_db, True)

        if telemetry_client:
            telemetry_client.set_node_identity(settings.ed25519_public, header_hash)

        # ----------- START NODE --------------
        async with asyncio.TaskGroup() as tg:
            # Telemetry (optional)
            if telemetry_client:
                tg.create_task(telemetry_client.run())
            # Networking - Block Imports, WP Processing, etc
            tg.create_task(start_node(str(host), int(port), is_builder))
            if rpc_flag:
                # RPC
                tg.create_task(rpc.run_task(debug=True, host=rpc_host, port=int(rpc_port), shutdown_trigger=rpc_shutdown_trigger))
            # Node Ops - Block Prod, Audit, Assurances, etc
            tg.create_task(operate(is_builder))

    except ExceptionGroup as eg:
        shutdown_event.set()
        logger.critical(f"Fatal error: {eg} ({type(eg).__name__})")
        # Log each sub-exception with full traceback
        for i, exc in enumerate(eg.exceptions):
            import traceback
            tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            logger.critical(f"Sub-exception {i+1}: {type(exc).__name__}: {exc}\n{tb_str}")
        # Close db connections
        if Path("data/tmp").exists():
            shutil.rmtree("data/tmp")
        settings.clear()
        raise asyncio.exceptions.CancelledError
    except Exception as e:
        shutdown_event.set()
        import traceback
        tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        logger.critical(f"Fatal error: {e} ({type(e).__name__})\n{tb_str}")
        # Close db connections
        if Path("data/tmp").exists():
            shutil.rmtree("data/tmp")
        settings.clear()
        raise asyncio.exceptions.CancelledError
    finally:
        loop = asyncio.get_running_loop()
        for t in asyncio.all_tasks(loop):
            t.cancel()
