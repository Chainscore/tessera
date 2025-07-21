from typing import Any

from jam.types.base.boolean import Boolean
from jam.types.base.byte_array import ByteArray128, ByteArray32


class VRF:
    def prove(self, message: ByteArray32) -> (ByteArray128, ByteArray128):
        pass

    def verify(self, proof: Any) -> Boolean:
        pass
