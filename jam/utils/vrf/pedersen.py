from typing import Any
from jam.types import ByteArray32, Boolean, ByteArray128


def PedersenVRF(IETFVRF):
    BLINDING_BASE = 123

    def prove(self, message: ByteArray32) -> (ByteArray128, ByteArray128):
        pass
    
    def verify(self, proof: Any) -> Boolean:
        pass

