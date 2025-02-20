from jam.RING_VRF.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
import os
import json

def test_bandersnatch_ed_public_key():
    data_dir = "tests/unit/vrf/data/ark-vrf/ietf"
    for file in os.listdir(data_dir):
        print(file)
        if not file.startswith("bandersnatch_ed"):
            continue
    
        with open(os.path.join(data_dir, file), "r") as f:
            data = json.loads(f.read())
            for i, vector in enumerate(data):
                generator = BandersnatchPoint(Bandersnatch_TE_Curve.GENERATOR_X, Bandersnatch_TE_Curve.GENERATOR_Y)
                secret_scalar = int.from_bytes(bytes.fromhex(vector["sk"]), "little") % Bandersnatch_TE_Curve.ORDER
                public_key = generator * secret_scalar
                public_key_hex = public_key.point_to_string().hex()
                assert public_key_hex == vector["pk"]
                print(f"✅ Testcase {i + 1} of {file}")
    
def test_bandersnatch_seals_public_key():
    data_dir = "tests/unit/vrf/data/colorful-notion"
    for file in os.listdir(data_dir):
        if not file.endswith("json"):
            continue
        with open(os.path.join(data_dir, file), "r") as f:
            vector = json.loads(f.read())
            generator = BandersnatchPoint(Bandersnatch_TE_Curve.GENERATOR_X, Bandersnatch_TE_Curve.GENERATOR_Y)
            secret_scalar = int.from_bytes(bytes.fromhex(vector["bandersnatch_priv"]), "little") % Bandersnatch_TE_Curve.ORDER
            public_key = generator * secret_scalar
            public_key_hex = public_key.point_to_string().hex()
            assert public_key_hex == vector["bandersnatch_pub"]
            print(f"✅ Passed Testcase {file}")
    
