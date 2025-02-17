from jam.RING_VRF.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
import os
import json

def test_bandersnatch_public_key():
    data_dir = "tests/unit/vrf/data"
    for file in os.listdir(data_dir):
        print(file)
        if not file.startswith("bandersnatch"):
            continue
    
        with open(os.path.join(data_dir, file), "r") as f:
            data = json.loads(f.read())
            for vector in data:
                generator = BandersnatchPoint(Bandersnatch_TE_Curve.GENERATOR_X, Bandersnatch_TE_Curve.GENERATOR_Y)
                secret_scalar = int.from_bytes(bytes.fromhex(vector["sk"]), "little")
                public_key = generator * secret_scalar
                print(public_key.x, public_key.y)
                public_key_hex = public_key.point_to_string().hex()

                print("expected point to string:", public_key.string_to_point("a1b1da71cc4682e159b7da23050d8b6261eb11a3247c89b07ef56ccd002fd38b"))
                # assert public_key_hex == vector["pk"]
    
