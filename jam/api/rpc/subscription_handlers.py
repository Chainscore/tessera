import asyncio

from jam.block import Block
from jam.api.rpc.broker import broker
from jam.models.state.delta import LookupTable, Timestamps, AccountMetadata
from tsrkit_types import Bytes
from jam.models.protocol.core import ServiceId, BlobLength
from jam.log_setup import network_logger as logger
from jam.models.protocol.crypto import HeaderHash, OpaqueHash
from jam.models.state.pi import Pi


def subscriptions_enabled() -> bool:
    try:
        from jam.settings import settings

        return bool(getattr(settings, "rpc_flag", False))
    except Exception:
        return False


def initial_subscription(method, params: list):
    if not subscriptions_enabled():
        return

    match method:
        case "subscribeServiceRequest":
            try:
                sid, pi_hash_list, pi_len, finality = params
                pi_hash = bytes(pi_hash_list)
                from jam.state.state import state
                from jam.finality.finality import Finality
                from jam.settings import settings

                account = state.delta[sid]
                lookup_key = LookupTable(Bytes[32](pi_hash), BlobLength(pi_len))
                value = account.lookup[lookup_key]
                block = Finality.load_final(settings.main_db) if finality else Finality.load_latest(
                    settings.main_db)
                method = f"subscribeServiceRequest:{sid}:{pi_hash_list}:{pi_len}:{finality}"
                asyncio.create_task(broker.publish(method, {"header_hash": list(block.header.hash()), "slot": int(block.header.slot),
                                           "value": value}))
            except Exception as e:
                logger.error("Error publishing subscribeServiceRequest", str(e))

            return

        case "subscribeServiceValue":
            try:
                sid, key_list, finality = params
                key = bytes(key_list)
                from jam.state.state import state
                from jam.finality.finality import Finality
                from jam.settings import settings

                value = state.delta[sid].storage.get(key)

                value = list(value) if value else None
                block = Finality.load_final(settings.main_db) if finality else Finality.load_latest(
                    settings.main_db)
                method = f"subscribeServiceValue:{sid}:{key_list}:{finality}"
                asyncio.create_task(broker.publish(method, {"header_hash": list(block.header.hash()), "slot": int(block.header.slot),
                                           "value": value}))
            except Exception as e:
                logger.error("Error publishing subscribeServiceValue", str(e))

            return

        case "subscribeServiceData":
            try:
                sid, finality = params
                from jam.state.state import state
                from jam.finality.finality import Finality
                from jam.settings import settings
                from jam.models.state.delta import AccountMetadata

                value = None
                if sid  in state.delta:
                    service = state.delta[sid].service
                    accountMetadata = AccountMetadata(
                        code_hash=service.code_hash,
                        balance=service.balance,
                        gas_limit=service.gas_limit,
                        min_gas=service.min_gas,
                        num_i=service.num_i,
                        num_o=service.num_o,
                        gratis_offset=service.gratis_offset,
                        created_at=service.created_at,
                        accumulated_at=service.accumulated_at,
                        parent_service=service.parent_service
                    )
                    value = list(accountMetadata.encode())
                block = Finality.load_final(settings.main_db) if finality else Finality.load_latest(
                    settings.main_db)
                method = f"subscribeServiceData:{sid}:{finality}"
                asyncio.create_task(
                    broker.publish(method, {"header_hash": list(block.header.hash()), "slot": int(block.header.slot),
                                            "value": value}))
            except Exception as e:
                logger.error("Error publishing subscribeServiceData", str(e))

            return

        case "subscribeServicePreimage":
            try:
                sid, pi_hash_list, finality = params
                from jam.state.state import state
                from jam.settings import settings
                from jam.finality.finality import Finality
                if settings.rpc_flag:
                    pi_hash = bytes(pi_hash_list)
                    blob = state.delta[sid].preimages[pi_hash]
                    value = list(blob) if blob else None
                    method = f"subscribeServicePreimage:{int(sid)}:{pi_hash_list}:{finality}"
                    block = Finality.load_final(settings.main_db) if finality else Finality.load_latest(
                        settings.main_db)
                    asyncio.create_task(broker.publish(method, {"header_hash": list(block.header.hash()), "slot": int(block.header.slot),
                                                      "value": value}))
            except Exception as e:
                logger.error("Error publishing subscribeServicePreimage", str(e))

            return

        case _:
            return

async def subscribe_sync_status(status: str):
    try:
        from jam.settings import settings
        if settings.rpc_flag:
            await broker.publish("subscribeSyncStatus", status)
    except Exception as e:
        logger.error("Error publishing subscribeSyncStatus", str(e))

async def subscribe_best_block(header_hash: HeaderHash):
    try:
        from jam.settings import settings
        if settings.rpc_flag:
            block = Block.load(header_hash, settings.main_db)
            if block:
                await broker.publish("subscribeBestBlock", {"header_hash": list(header_hash), "slot": int(block.header.slot)})
            else:
                logger.warning("Trying to publish best block, but not found in store", header_hash=header_hash.hex())
    except Exception as e:
        logger.error("Error publishing subscribeBestBlock", str(e))

async def subscribe_finalized_block(header_hash: HeaderHash):
    try:
        from jam.settings import settings
        from jam.api.rpc.broker import broker
        if settings.rpc_flag:
            block = Block.load(header_hash, settings.main_db)
            if block:
                await broker.publish("subscribeFinalizedBlock", {"header_hash": list(header_hash), "slot": int(block.header.slot)})
            else:
                logger.warning("Trying to publish finalized block, but not found in store", header_hash=header_hash.hex())
    except Exception as e:
        logger.error("Error publishing subscribeFinalizedBlock", str(e))

async def subscribe_service_value(sid: ServiceId, key: Bytes, value: list | None):
    try:
        key_list = list(key)
        method = f"subscribeServiceValue:{int(sid)}:{key_list}"
        await pub(method, value)
    except Exception as e:
        logger.error("Error publishing subscribeServiceValue", str(e))

async def subscribe_service_request(sid: ServiceId, pi_hash: OpaqueHash, pi_len: BlobLength, value: Timestamps | None):
    try:
        pi_hash_list = list(pi_hash)
        method = f"subscribeServiceRequest:{int(sid)}:{pi_hash_list}:{int(pi_len)}"
        await pub(method, value)
    except Exception as e:
        logger.error("Error publishing subscribeServiceRequest", str(e))

async def subscribe_statistics(pi: Pi):
    try:
        value = list(pi.encode()) if pi else None
        method = f"subscribeStatistics"
        await pub(method, value)
    except Exception as e:
        logger.error("Error publishing subscribeStatistics", str(e))

async def subscribe_service_data(sid: ServiceId, account_metadata: AccountMetadata):
    try:
        value = list(account_metadata.encode()) if account_metadata else None
        method = f"subscribeServiceData:{int(sid)}"
        await pub(method, value)
    except Exception as e:
        logger.error("Error publishing subscribeServiceData", str(e))

async def subscribe_service_preimage(sid: ServiceId, pi_hash: OpaqueHash, blob: Bytes):
    try:
        pi_hash_list = list(pi_hash)
        value = list(blob) if blob else None
        method = f"subscribeServicePreimage:{int(sid)}:{pi_hash_list}"
        await pub(method, value)
    except Exception as e:
        logger.error("Error publishing subscribeServicePreimage", str(e))

async def pub(method: str, value: list | None):
    from jam.settings import settings
    from jam.finality.finality import Finality
    if settings.rpc_flag:
        for finality in [True, False]:
            publish_method = f"{method}:{finality}"
            block = Finality.load_final(settings.main_db) if finality else Finality.load_latest(
                settings.main_db)
            if block:
                await broker.publish(publish_method, {"header_hash": list(block.header.hash()), "slot": int(block.header.slot),
                                          "value": value})
