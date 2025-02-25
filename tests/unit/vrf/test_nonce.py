from jam.ring_vrf.curve.specs.bandersnatch import Bandersnatch_TE_Curve, BandersnatchPoint
from jam.ring_vrf.ietf.ietf import IETF_VRF
from .test_e2c import BigInt, process_field_elements

def test_nonce():
    data = b""
    
    input_point = BandersnatchPoint.encode_to_curve(data, b"")
    assert input_point.x == 23177656040451240103938304363591821492951015767333712630108457573549787226093
    assert input_point.y == 78284803470694319592756962928195357281227187761612519520494432739017353925

    vrf = IETF_VRF(Bandersnatch_TE_Curve)

    secret_key = int.from_bytes(bytes.fromhex("3d6406500d4009fdf2604546093665911e753f2213570a29521fd88bc30ede18"), "little")

    nonce = vrf.generate_nonce(secret_key, input_point)
    
    # Test vector from specification
    assert nonce == process_field_elements([BigInt([16155995435483652935, 10762397538198134741, 9599248960853550599, 1125554040602686858])])[0]


