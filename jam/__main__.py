import asyncio
import json
import logging
import os
import time

from asyncio import CancelledError
from dotenv import load_dotenv
from jam.operations import operate
from jam.logging import setup_logging, logger
from jam.network.base.certificate import generate_san
from jam.utils.chainspec import chain_config
from jam.settings import setup_setting
from jam.finality.finality import Finality
from jam.network.peer import Peer
from jam.network.node import setup_node
# from jam.operations.utils.state_update import update_state
from jam.state.state import setup_state
from jam.block import Block
from jam.utils.constants import GENESIS_TS, SLOT_PERIOD, EPOCH_LENGTH
from tests.integration.utils.state_update import update_state

TIMESLOT = 0

async def main(
    genesis_path: str,
    env: str,
    start_genesis: bool,
    theme: str,
    is_builder: bool,
    is_validator: bool,
) -> None:
    # ---------- SETUP LOGGING ----------
    genesis_ts = GENESIS_TS  # Actual Genesis time for JAM Common Era
    init_ts = int((time.time() - genesis_ts) // SLOT_PERIOD)
    init_ep = int(init_ts // EPOCH_LENGTH)

    global TIMESLOT
    TIMESLOT = init_ts

    # ---------- LOAD ENVIRONMENT ----------
    load_dotenv(".env")
    load_dotenv(env, override=True)

    name = os.environ["NODE_NAME"]
    port = os.environ["PORT"]
    seed = os.environ["SEED"]
    host = os.environ["HOST"]

    if not name or not port or not host or not seed:
        raise ValueError(f"Missing node info in {env}")

    # ---------- SETUP LOGGING ----------
    environment = os.environ.get("ENVIRONMENT", "development")
    log_level = os.environ.get("LOG_LEVEL", None)

    setup_logging(
        theme=theme,
        node_name=name,
        environment=environment,
        min_level=getattr(logging, log_level.upper()) if log_level else None,
    )

    # ---------- SETUP SETTINGS ----------
    settings = setup_setting(
        name=name, port=int(port), seed=int(seed), data_path="data/"
    )

    main_db = settings.main_db

    logger.info(
        """                                                                                                                                                                                                                                                                                                                            
                                                                                                                        0000                                                                                                                                                    0000           400                                                
                                                                                                                       0000000                                                                                                                                                9000000         000000                                              
                                                                                                                       000000000                                                                                                                                              0000000        0000000                                              
                                       700000000000007                                                                  000000000                                                                                                                                              0000000     00000000                                               
                                     0006222222222226000                                                                  00000000                                                                                                                                             0000000000000000000                                                
                                    002222222222222222200                                                                  00000000                                                                                                                                              0000000000000000                                                 
                                    005222222222222222500                                                                    0000000                                                                                                                                              0000000000000                                                   
                           000000    0009222222222229000    400000                                                            0000000                                                                                                                                                   7                                                         
                        0009222500      0000000000000      0042229000                                                          0000000                                                                                                                                                                                                            
                       00522222220                         02222222500              00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000               
                     3092222222220                         0222222222900           000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000               
                    30422222222290                         09222222222500          00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000                
                    0422222222260                           0622222222250                 0000000              0000000         0000000                                                         0000000                        0000000                            0000000           0000000                         0000000                        
                   0022222222260                             0922222222200                0000000              0000000        00000000                                                        0000000                        9000000                             0000000          0000000                          0000000                        
                   0922222225003                              005222222260                000000              00000000        0000000                                                         0000000                        0000000                000000000   0000000           0000000                         0000000                         
                   90522225800                                 00052222500               0000000              0000000         0000000             10000                        00000000000   00000007   1000                 0000000           000000000000000000000000           000000                          0000000                         
                    00000000                                     00000000                0000000             90000000        00000000        000000000000000   000000000000 0000000000000000000000000000000000000           0000000          0000000000000000000000000           0000000             0000000000000000000                          
                                                                                         000000              0000000         0000000       000000000000000000000000000000000000000000000000000000000000000000000000         0000000        00000000000000000000000000            0000001         00000000000000000000000                          
                                                                                        0000000              0000000        00000000      00000000000000000000000000000000000000000     0000000000000000000000000000        0000000        00000000                             0000000        000000000000000000000000                           
                      0001                                         1000                 0000000             0000000         0000000      000000007        000000000     00000000            0000000004      00000000       0000000        00000008                              0000000      000000000000013  00000000                            
                    008490000                                   000094800               0000000            00000000        00000000     00000000          0000000      30000000            00000000          00000000      0000000        00000000                             0000000      0000000000                                            
                   00222222500                                 00522222200               0000000         0000000009        0000000     10000000          0000000       0000000             0000000            0000000      000000          0000000000000000000000              0000000     000000005                                              
                   0922222222600                             0062222222290               0000000000000000000000000         0000000     00000000          0000000       00000005           00000000           00000000     0000000           000000000000000000000000          0000000      0000000                                                
                   20222222222500                           00522222222205                000000000000000000000000        00000000     00000000          000000         00000000        0000000009          00000000      0000000            0000000000000000000000000        0000000     00000000                                                
                    09222222222504                         40522222222290                   000000000000000000000         0000000       0000000          000000         0000000000000000000000000         000000000      0000000                 0000000006 0000000000        000000      00000000                                                
                     0822222222240                         0422222222290                       00000000   0000000         0000000       00000000          0000           500000000000000000000000     000000000000       0000000      0000                     00000000      0000000      90000000                                                
                      005222222220                         022222222200                                  00000000        00000000        000000000                         000000000000000000000     00000000000        0000000      0000000                   00000000      0000000       00000000                000007                         
                       00852222250         0000000         05222222800                                   0000000         0000000          0000000007                          90000000   0000000     000000000          0000000      0000000000                0000000      0000000         000000000           000000000                         
                         000855000     0000864544800007    000658000                                     0000000        00000000           00000000000                                  0000000                         0000008        0000000000000       00000000000      0000000          0000000000000000000000000000                         
                            0000     0062222222222222400     5000                                       00000003        0000000              00000000000                                0000000                        0000000           0000000000000000000000000008       000000            0000000000000000000000000                           
                                    082222222222222222290                                               0000000         0000000                000000000                                000000                          000000             000000000000000000000000         000000              00000000000000000000                              
                                    009222222222222222600                                                 000             000                     00000                                   000                                                  00000000000000000             000                    000000000000                                  
                                      00095222222259000                                                                                                                                                                                                                                                                                           
                                         00000000000                                                                                                                                                                                                                                                                                              
        """,
        name=name,
        port=port,
        ts=init_ts,
        epoch=init_ep,
        spec=chain_config.name,
    )

    try:
        # -------------- SETUP STATE -------------
        # Set genesis state
        dev_spec = json.load(open(genesis_path))
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
        state = setup_state(settings.state_db, genesis_path)
        state.store.disable_cache()

        # TODO: Remove Later
        update_state(state)

        # ----------- SETUP NETWORKING ------------
        peers = [Peer(data=val) for val in state.kappa if val.metadata.port != port]

        tsr_node = setup_node(
            name,
            int(port),
            peers,
            host=str(host),
            is_bd=is_builder,
            is_val=is_validator,
        )

        # ------------ SET GENESIS BLOCK ------------
        block = Block.decode(bytes.fromhex(dev_spec["genesis_header"]))
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)
        Finality.finalise(header_hash, main_db)

        # ----------- START NODE --------------
        async with asyncio.TaskGroup() as tg:
            # Networking - Block Imports, WP Processing, etc
            tg.create_task(tsr_node.initialize())
            # RPC
            # tg.create_task(rpc.run_task(debug=True, host="0.0.0.0", port=5001))
            # Node Ops - Block Prod, Audit, Assurances, etc

            tg.create_task(operate(is_builder))

    except CancelledError:
        logger.info(
            "JAM node shutting down gracefully",
            node_name=name,
            port=port,
            reason="cancelled_tasks",
        )

        settings.clear()

    except KeyboardInterrupt:
        logger.info(
            "JAM node shutting down gracefully",
            node_name=name,
            port=port,
            reason="keyboard_interrupt",
        )

    except Exception as e:
        logger.critical(
            "JAM node fatal error",
            node_name=name,
            port=port,
            error=str(e)[:200],
            error_type=type(e).__name__,
        )
        # Close db connections
        settings.clear()

        raise


