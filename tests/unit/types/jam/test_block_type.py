from jam.block import Block

def test_random_blocks():
    block_a = Block.from_random()
    block_b = Block.from_random()
    assert block_a != block_b