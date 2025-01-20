from jam.types.protocol.crypto import Ed25519Signature, OpaqueHash
from jam.types.extrinsics.assurances import AvailAssurance, AvailBitField

def test_jam_types_json():
    data = {"anchor": "0x0cffbf67aae50aeed3c6f8f0d9bf7d854ffd87cef8358cbbaa587a9e3bd1a776", "bitfield": "0x01", "validator_index": 1, "signature": "0x2d8ec7b235be3b3cbe9be3d5ff36f082942102d64a0dc5953709a95cca55b58b1af297f534d464264be77477b547f3c596b947edbca33f6631f1aa188d25a38b"}
    model = AvailAssurance.from_json(data)  

    #Compare them 
    assert model.anchor == OpaqueHash("0x0cffbf67aae50aeed3c6f8f0d9bf7d854ffd87cef8358cbbaa587a9e3bd1a776")
    assert model.bitfield == AvailBitField("0x01")
    assert model.validator_index == 1
    assert model.signature == Ed25519Signature("0x2d8ec7b235be3b3cbe9be3d5ff36f082942102d64a0dc5953709a95cca55b58b1af297f534d464264be77477b547f3c596b947edbca33f6631f1aa188d25a38b")
