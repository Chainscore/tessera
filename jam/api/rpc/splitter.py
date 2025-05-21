import asyncio
import tempfile
from numpy import block
from broker import broker
from jam.db.kv import KVStore
from jam.state.state import State, state
from jam.types.block import Block
from jam.types.protocol import service
from jam.types.protocol.core import TimeSlot
from jam.consensus.grandpa.finality import Finality
from jam.config.data_stores import main_db #swithing to main_db
from jam.types.header import Header

async def split_them_messages():
    while True:
        await broker.publish("news", {"Breaking news" : "Something happened!"})
        await asyncio.sleep(2)

async def subscribe_best_block():
    last_slot = None
    last_hash = None
    while True:
        current_hash = Header.__hash__(Block.header)
        current_slot = int(Block.header.slot)
        if last_slot != current_slot or last_hash != current_hash:
            await broker.publish("subscribeBestBlock", {"Hash" : current_hash, "Slot" : current_slot})
            last_slot = current_slot
            last_hash = current_hash


async def subscribe_finalized_block():
    last_slot = None
    last_hash = None
    while True:
        finality_block = Finality.load_final(main_db)
        current_hash = Header.__hash__(finality_block.header)
        current_slot = int(finality_block.header.slot)
        if last_slot != current_slot or last_hash != current_hash:
            await broker.publish("subscribeFinalizedBlock", {"Hash" : Header.__hash__(finality_block.header), "Slot" : int(finality_block.header.slot)})
            last_slot = current_slot
            last_hash = current_hash


async def subscribe_statistics():
    last_state = None
    while True:
        current_state = state 
        if(last_state != current_state):
            await broker.publish("subscribeStatistics", {"blob": state.pi})
            last_state = current_state  


async def subscribe_service_data():
    last_state = None
    while True:
        current_state = state 
        if(last_state != current_state):
            await broker.publish("subscribeServiceData", {"blob" : state.delta})
            last_state = current_state
        
        await asyncio.sleep(2)

async def subscribe_service_value():
    last_state = None
    while True:
        current_state = state 
        if(last_state != current_state):
            await broker.publish("subscribeServiceValue", {"blob" : state.delta})
            last_state = current_state
        
        

async def subscribe_service_preimage():
    last_state = None
    while True:
        current_state = state
        if(last_state != current_state):
            await broker.publish("subscribeServicePreimage", {"blob" : state.delta})
            last_state = current_state
       

async def subscribe_service_request():  
    last_state = None
    while True:
        current_state = state 
        if(last_state != current_state):
            await broker.publish("subscribeServiceRequest", {"blob" : state.delta})
            last_state = current_state