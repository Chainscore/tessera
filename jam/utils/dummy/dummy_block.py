from jam.types.block import Block
from jam.utils.dummy.dummy_extrinsics import create_dummy_extrinsics
from jam.utils.dummy.dummy_header import create_dummy_header


def create_dummy_block() -> Block:
    return Block(header=create_dummy_header(), extrinsic=create_dummy_extrinsics())
