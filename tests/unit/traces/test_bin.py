from tsrkit_types import Bytes, U32


def test_bin(db_path):
    root = Bytes[32](
        bytes.fromhex(
            "e1b25f53abb29efec7a71fa91a89357f6612d1a40b86288c92b4a10c958e8aa7"
        )
    )

    data = U32(4).encode() + root.encode()
    print("ENCODED DATA", data)
