from rockstore import RockStore
from jam.types.block import Block
from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import Hash


class Finality:

    FINAL_KEY = bytes(Hash.blake2b(b"FINAL_BLOCK"))
    LATEST_KEY = bytes(Hash.blake2b(b"LATEST_BLOCK"))

    @classmethod
    def finalise(cls, slot: TimeSlot, kv: RockStore): 
        # TODO Add grandpa validation logic
        kv.put(cls.FINAL_KEY, slot.encode())

    @classmethod
    def set_head(cls, slot: TimeSlot, kv: RockStore):
        kv.put(cls.LATEST_KEY, slot.encode())

    @classmethod
    def load_final(cls, kv: RockStore) -> Block:
        slot = TimeSlot(0)
        slot_bytes = kv.get(cls.FINAL_KEY)
        if slot_bytes:
            slot, _ = TimeSlot.decode_from(slot_bytes)
        return Block.load(slot, kv)

    @classmethod
    def load_latest(cls, kv: RockStore):
        slot = TimeSlot(0)
        slot_bytes = kv.get(cls.LATEST_KEY)
        if slot_bytes:
            slot, _ = TimeSlot.decode_from(slot_bytes)
        return Block.load(slot, kv)
