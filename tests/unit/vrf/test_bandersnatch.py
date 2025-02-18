from jam.RING_VRF.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
import os
import json

def test_bandersnatch_public_key():
    data_dir = "tests/unit/vrf/data"
    for file in os.listdir(data_dir):
        print(file)
        if not file.startswith("bandersnatch"):
            continue
    
        # with open(os.path.join(data_dir, file), "r") as f:
        #     data = json.loads(f.read())
        #     for vector in data:
        #         generator = BandersnatchPoint(Bandersnatch_TE_Curve.GENERATOR_X, Bandersnatch_TE_Curve.GENERATOR_Y)
        #         secret_scalar = int.from_bytes(bytes.fromhex(vector["sk"]), "little")
        #         public_key = generator * secret_scalar
        #         # public_key.x = public_key._x_recover(public_key.y)
        #         # public_key.x = public_key.curve.PRIME_FIELD - public_key.x  # Flip x if the bit doesn't match
        #         # print(public_key.x, public_key.y)
        #         public_key.x = Bandersnatch_TE_Curve.PRIME_FIELD - public_key.x
        #         print("New x:", public_key.x)
        #         public_key_hex = public_key.point_to_string().hex()


        #         expected_point = public_key.string_to_point(vector["pk"])
        #         print("expected point to string:", expected_point)
        #         # assert public_key.y == expected_point[1]
        #         # assert public_key_hex == vector["pk"]
        #         print("✅ ", file)
    
