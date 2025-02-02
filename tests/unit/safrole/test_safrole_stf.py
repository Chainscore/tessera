from tests.unit.safrole.types import get_testcases_starting_with

def test_safrole_stf():
    # Read all files in the tests/unit/safrole/data directory
    vectors = get_testcases_starting_with(limit=100)
    print(len(vectors))