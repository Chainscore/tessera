
from jam.utils.shuffle import shuffle
from jam.types import  decodable_vector, U32, Vector
import json
from pathlib import Path

@decodable_vector(element_type=U32)
class U32Vector(Vector): ...


def test_shuffle():
    test_dir = Path(__file__).parent

    # Load test vectors
    with open(test_dir / "shuffle_tests.json", "r") as f:
        vectors_json = json.load(f)

        for i in range(len(vectors_json)):
            array: U32Vector = U32Vector([])
            for j in range(vectors_json[i]['input']):
                array.append(U32(j))
            print(f"Testing vector #{i}")
            numbers = shuffle(vectors_json[i]["entropy"], array)
            assert numbers == vectors_json[i]["output"]
            print(f"✅ Passed vector #{i}")



