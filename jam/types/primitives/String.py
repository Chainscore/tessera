from jam.types.Codec import Codec

class String(str, Codec[str]):
    def encode(self) -> bytes:
        return self.encode()
