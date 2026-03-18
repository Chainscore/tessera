import json
from pathlib import Path

import pytest

from jam.block.header import Header

pytestmark = pytest.mark.unit


def test_genesis_header_hash():
    spec_path = Path(__file__).parents[3] / "dev-spec.json"
    genesis = json.loads(spec_path.read_text())
    dec_header = Header.decode(bytes.fromhex(genesis["genesis_header"]))
    assert dec_header.encode().hex() == genesis["genesis_header"]
