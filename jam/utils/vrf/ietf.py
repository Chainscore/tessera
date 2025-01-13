from typing import Any
from jam.types.base.boolean import Boolean
from jam.types.base.byte_array import ByteArray32, ByteArray128
from jam.utils.vrf.base import VRF
from .utils import str_to_crv_ell2

class IETFVRF(VRF):
    GENERATOR_X = 123
    GENERATOR_Y = 321

    def prove(self, message: ByteArray32) -> (ByteArray128, ByteArray128):
        # TODO: Implement IETF VRF
        str_to_crv_ell2()
        pass
    
    def verify(self, proof: Any) -> Boolean:
        # TODO: Implement IETF VRF
        pass