from typing import List

from jam.merklization import MMRFunctions, MMR, OptionHash
from jam.types import ByteArray32, Null
from jam.types.protocol.crypto import Hash
from tests.unit.recent_history.types import get_testcases_starting_with, Testcase
from tests.unit.recent_history.transformations import vector_transition

def test_tiny():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(limit=4)
    for i, vector in enumerate(vectors):

        assert vector_transition(vector)
        print(f"Passed testcase #{i + 1}")


def test_recent_history_demo():

    mmr_functions = MMRFunctions()

    # Tests

    # Test Case 1:

    h1: ByteArray32 = ByteArray32("0x8720b97ddd6acc0f6eb66e095524038675a4e4067adc10ec39939eaefc47d842")
    mmr1 = MMR([])
    res1 = mmr_functions.append_fn(mmr1, h1, Hash.keccak256)

    op1_val1 = OptionHash(ByteArray32("0x8720b97ddd6acc0f6eb66e095524038675a4e4067adc10ec39939eaefc47d842"))

    op1 = MMR([op1_val1])

    print("Test Case 1", res1 == op1)

    # Test Case 2:

    h2: ByteArray32 = ByteArray32("0x7507515a48439dc58bc318c48a120b656136699f42bfd2bd45473becba53462d")

    val2_1 = OptionHash(ByteArray32("0x8720b97ddd6acc0f6eb66e095524038675a4e4067adc10ec39939eaefc47d842"))

    mmr2 = MMR([val2_1])

    op2_val1 = OptionHash(Null)
    op2_val2 = OptionHash(ByteArray32("0x7076c31882a5953e097aef8378969945e72807c4705e53a0c5aacc9176f0d56b"))
    op2 = MMR([op2_val1, op2_val2])
    res2 = mmr_functions.append_fn(mmr2, h2, Hash.keccak256)

    print("Test Case 2", res2 == op2)

    # Test Case 3:

    h3: ByteArray32 = ByteArray32("0x8223d5eaa57ccef85993b7180a593577fd38a65fb41e4bcea2933d8b202905f0")

    val3_1 = OptionHash(ByteArray32("0xf986bfeff7411437ca6a23163a96b5582e6739f261e697dc6f3c05a1ada1ed0c"))
    val3_2 = OptionHash(ByteArray32("0xca29f72b6d40cfdb5814569cf906b3d369ae5f56b63d06f2b6bb47be191182a6"))
    val3_3 = OptionHash(ByteArray32("0xe17766e385ad36f22ff2357053ab8af6a6335331b90de2aa9c12ec9f397fa414"))

    mmr3 = MMR([val3_1, val3_2, val3_3])

    op3_val1 = OptionHash(Null)
    op3_val2 = OptionHash(Null)
    op3_val3 = OptionHash(Null)
    op3_val4 = OptionHash(ByteArray32("0x658b919f734bd39262c10589aa1afc657471d902a6a361c044f78de17d660bc6"))
    op3 = MMR([op3_val1, op3_val2, op3_val3, op3_val4])
    res3 = mmr_functions.append_fn(mmr3, h3, Hash.keccak256)

    print("Test Case 3", res3 == op3)

    # Test Case 4:

    h4: ByteArray32 = ByteArray32("0xa983417440b618f29ed0b7fa65212fce2d363cb2b2c18871a05c4f67217290b0")

    val4_1 = OptionHash(Null)
    val4_2 = OptionHash(Null)
    val4_3 = OptionHash(Null)
    val4_4 = OptionHash(ByteArray32("0x658b919f734bd39262c10589aa1afc657471d902a6a361c044f78de17d660bc6"))

    mmr4 = MMR([val4_1, val4_2, val4_3, val4_4])

    op4_val1 = OptionHash(ByteArray32("0xa983417440b618f29ed0b7fa65212fce2d363cb2b2c18871a05c4f67217290b0"))
    op4_val2 = OptionHash(Null)
    op4_val3 = OptionHash(Null)
    op4_val4 = OptionHash(ByteArray32("0x658b919f734bd39262c10589aa1afc657471d902a6a361c044f78de17d660bc6"))
    op4 = MMR([op4_val1, op4_val2, op4_val3, op4_val4])


    res4 = mmr_functions.append_fn(mmr4, h4, Hash.keccak256)
    print("Test Case 4", res4 == op4)
