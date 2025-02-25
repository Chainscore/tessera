import os
import json
from jam.ring_vrf.curve.specs.bandersnatch import Bandersnatch_TE_Curve
from jam.ring_vrf.ietf.ietf import IETF_VRF

def test_bandersnatch_ed_sha512_ell2_ietf():
    ...
    data_dir = "tests/unit/vrf/data/ark-vrf/ietf"
    limit = 10000
    for i, file in enumerate(os.listdir(data_dir)):
        print(file)
        if i >= limit:
            break
        if not file.startswith("bandersnatch_ed_sha512_ell2_ietf"):
            continue
        with open(os.path.join(data_dir, file), "r") as f:
            data = json.loads(f.read())
            for i, vector in enumerate(data):
                print(vector)
                secret_scalar = int.from_bytes(bytes.fromhex(vector["sk"]), "little") % Bandersnatch_TE_Curve.ORDER
                vrf = IETF_VRF(Bandersnatch_TE_Curve)
                output_point, proof = vrf.proof(bytes.fromhex(vector["alpha"]), secret_scalar, bytes.fromhex(vector["ad"]))
                assert output_point.point_to_string().hex() == vector["gamma"]
                # assert proof[0] == int.from_bytes(bytes.fromhex(vector["proof_c"]), "little")
                # assert proof[1] == int.from_bytes(bytes.fromhex(vector["proof_s"]), "little")
                print(f"✅ Testcase {i + 1} of {file}")
