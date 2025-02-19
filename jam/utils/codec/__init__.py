"""Type-safe serialization framework 📦

Core:
* Codec[T]: Generic codec interface
* Codable: Base class for encodable types
* primitives: Basic type codecs
* composite: Container type codecs
* decorators: Automatic codec generation
* errors: Error handling
"""

from .codec import Codec
from .codable import Codable
from .errors import CodecError, BufferError, EncodeError, DecodeError

__all__ = [
    "Codec",
    "Codable",
    "CodecError",
    "BufferError",
    "EncodeError",
    "DecodeError",
]

__version__ = "1.0.0"
