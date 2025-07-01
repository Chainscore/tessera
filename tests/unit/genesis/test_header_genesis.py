import json

from jam.types.block.header import Header


def test_genesis_header_hash():
    genesis = json.load(open("dev-spec.json"))
    dec_header = Header.decode(bytes.fromhex(genesis["genesis_header"]))
    assert dec_header.encode().hex() == genesis["genesis_header"]
    print(dec_header.hash().hex())
