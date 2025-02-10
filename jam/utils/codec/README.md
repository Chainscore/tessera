# TsrCodec

Implementations for serializing and deserializing data types according to the JAM specs.

## Overview

The codec system provides:

-   Type-safe encoding and decoding of data structures
-   Support for primitive and composite types
-   Extensible registry for custom codec implementations
-   Automatic type inference and validation

## How to Use

This guide explains how to use the TsrCodec library to encode and decode various data types, including custom types.

### Basic Usage

The core functions for encoding and decoding are `encode` and `decode`. These functions automatically use the appropriate codec based on the type of the value being encoded or decoded.

```python
from jam.utils.codec import encode, decode
from jam.utils.codec.primitives.integers import U32
from jam.utils.codec.primitives.strings import string_codec
from jam.utils.codec.composite.options import OptionCodec
from jam.utils.codec.composite.vectors import VectorCodec

# Encoding
encoded_number = encode(U32(42))  # Uses U32 codec
encoded_string = encode("hello") # Uses StringCodec

# Decoding
decoded_number, _ = u32_codec.decode_from(encoded_number)
decoded_string, _ = string_codec.decode_from(encoded_string)

print(f"Encoded number: {encoded_number}")
print(f"Decoded number: {decoded_number}")
print(f"Encoded string: {encoded_string}")
print(f"Decoded string: {decoded_string}")
```

### Supported Data Types

The TsrCodec library supports the following data types:

| Type          | Description              | Codec                   | Status |
| ------------- | ------------------------ | ----------------------- | ------ |
| `bool`        | Boolean value            | `BooleanCodec`          | ✅     |
| `u8`          | 8-bit unsigned integer   | `u8_codec`              | ✅     |
| `u16`         | 16-bit unsigned integer  | `u16_codec`             | ✅     |
| `u32`         | 32-bit unsigned integer  | `u32_codec`             | ✅     |
| `u64`         | 64-bit unsigned integer  | `u64_codec`             | ✅     |
| `u128`        | 128-bit unsigned integer | `u128_codec`            | ✅     |
| `u256`        | 256-bit unsigned integer | `u256_codec`            | ✅     |
| `str`         | UTF-8 string             | `StringCodec`           | ✅     |
| `Array[T,N]`  | Fixed-length array       | `ArrayCodec[T, N]`      | ✅     |
| `Option[T]`   | Optional value           | `OptionCodec[T]`        | ✅     |
| `Vector[T]`   | Dynamic-length array     | `VectorCodec[T]`        | ✅     |
| `Dict[K,V]`   | Key-value mapping        | `DictionaryCodec[K, V]` | ✅     |
| `BitSequence` | Sequence of bits         | `BitSequenceCodec`      | ✅     |

### Encoding and Decoding Composite Types

Composite types are encoded by combining the encodings of their constituent elements.

#### Arrays

```python
from jam.utils.codec import encode, decode
from jam.utils.codec.composite.arrays import ArrayCodec
from jam.utils.codec.primitives.integers import u8_codec

# Create an array codec for an array of 5 u8 integers
array_codec = ArrayCodec(5, u8_codec)

# Encode an array
numbers = [1, 2, 3, 4, 5]
encoded_array = array_codec.encode(numbers)

# Decode the array
decoded_array, _ = array_codec.decode_from(encoded_array)

print(f"Encoded array: {encoded_array}")
print(f"Decoded array: {decoded_array}")
```

#### Options

```python
from jam.utils.codec import encode, decode
from jam.utils.codec.composite.options import OptionCodec
from jam.utils.codec.primitives.strings import string_codec

# Create an option codec for an optional string
option_codec = OptionCodec(str, string_codec)

# Encode an optional value (Some)
maybe_name = "Alice"
encoded_some = option_codec.encode(maybe_name)

# Encode an optional value (None)
maybe_none = None
encoded_none = option_codec.encode(maybe_none)

# Decode the optional values
decoded_some, _ = option_codec.decode_from(encoded_some)
decoded_none, _ = option_codec.decode_from(encoded_none)

print(f"Encoded Some: {encoded_some}")
print(f"Decoded Some: {decoded_some}")
print(f"Encoded None: {encoded_none}")
print(f"Decoded None: {decoded_none}")
```

#### Vectors

```python
from jam.utils.codec import encode, decode
from jam.utils.codec.composite.vectors import VectorCodec
from jam.utils.codec.primitives.integers import u32_codec

# Create a vector codec for a vector of u32 integers
vector_codec = VectorCodec(int, u32_codec)

# Encode a vector
numbers = [10, 20, 30, 40]
encoded_vector = vector_codec.encode(numbers)

# Decode the vector
decoded_vector, _ = vector_codec.decode_from(encoded_vector)

print(f"Encoded vector: {encoded_vector}")
print(f"Decoded vector: {decoded_vector}")
```

#### Dictionaries

```python
from jam.utils.codec import encode, decode
from jam.utils.codec.composite.dictionaries import DictionaryCodec
from jam.utils.codec.primitives.strings import string_codec
from jam.utils.codec.primitives.integers import u8_codec

# Create a dictionary codec for a dictionary with string keys and u8 values
dictionary_codec = DictionaryCodec(str, int, string_codec, u8_codec)

# Encode a dictionary
data = {"apple": 1, "banana": 2, "cherry": 3}
encoded_dict = dictionary_codec.encode(data)

# Decode the dictionary
decoded_dict, _ = dictionary_codec.decode_from(encoded_dict)

print(f"Encoded dictionary: {encoded_dict}")
print(f"Decoded dictionary: {decoded_dict}")
```

### Encoding and Decoding Custom Types

To encode and decode custom types, you need to define `encode_size`, `encode_into`, and `decode_from` methods for your class. These methods should use the appropriate codecs for the attributes of your class.

**Example: UserProfile**

```python
from typing import Optional, List, Tuple, Union
from dataclasses import dataclass
from jam.utils.codec.primitives.strings import string_codec
from jam.utils.codec.primitives.integers import u32_codec
from jam.utils.codec.composite.options import OptionCodec
from jam.utils.codec.composite.vectors import VectorCodec
from jam.utils.codec.base import Codec, EncodeError, DecodeError
from jam.utils.codec.utils import check_buffer_size, ensure_size

@dataclass
class UserProfile:
    user_id: int  # U32
    username: str
    bio: Optional[str]
    interests: List[str]

    def encode_size(self) -> int:
        size = 0
        size += u32_codec.encode_size(self.user_id)
        size += string_codec.encode_size(self.username)
        size += OptionCodec(str, string_codec).encode_size(self.bio)
        size += VectorCodec(str, string_codec).encode_size(self.interests)
        return size

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        total_size = self.encode_size()
        check_buffer_size(buffer, total_size, offset)

        current_offset = offset
        current_offset += u32_codec.encode_into(self.user_id, buffer, current_offset)
        current_offset += string_codec.encode_into(self.username, buffer, current_offset)
        current_offset += OptionCodec(str, string_codec).encode_into(self.bio, buffer, current_offset)
        current_offset += VectorCodec(str, string_codec).encode_into(self.interests, buffer, current_offset)
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple['UserProfile', int]:
        current_offset = offset
        user_id, size = u32_codec.decode_from(buffer, current_offset)
        current_offset += size
        username, size = string_codec.decode_from(buffer, current_offset)
        current_offset += size
        bio, size = OptionCodec(str, string_codec).decode_from(buffer, current_offset)
        current_offset += size
        interests, size = VectorCodec(str, string_codec).decode_from(buffer, current_offset)
        current_offset += size

        return UserProfile(user_id, username, bio, interests), current_offset - offset

# Example usage
profile = UserProfile(
    user_id=12345,
    username="johndoe",
    bio="Software Engineer",
    interests=["coding", "music", "hiking"]
)

encoded_profile = bytearray(profile.encode_size())
profile.encode_into(encoded_profile)
decoded_profile, _ = UserProfile.decode_from(encoded_profile)

print(f"Encoded profile: {encoded_profile}")
print(f"Decoded profile: {decoded_profile}")
```

### Vector Length Encoding

Vector lengths use a variable-length encoding scheme:

-   `0x00-0xFC`: Direct value (1 byte)
-   `0xFF`: u16 value (3 bytes)
-   `0xFE`: u24 value (4 bytes)
-   `0xFD`: u32 value (5 bytes)

### Protocol Specification

#### Primitive Types

-   **Boolean**: Single byte, `0` for false, `1` for true
-   **Integers**: Little-endian encoded bytes
-   **Strings**: Length-prefixed UTF-8 bytes

#### Composite Types

-   **Arrays**: Fixed length, concatenated elements
-   **Options**: 1-byte tag (`0` = None, `1` = Some) followed by value if present
-   **Vectors**: Length prefix followed by concatenated elements
-   **Tuples**: Concatenated elements in order
-   **Dictionaries**: Length prefix followed by sorted key-value pairs

#### Type Safety

The codec system enforces:

-   Type checking during encoding/decoding
-   Buffer size validation
-   Value range constraints
-   Array length constraints

### Testing Status

-   [x] Primitive type codecs
-   [x] Array codec
-   [x] Option codec
-   [x] Vector codec
-   [x] Tuple codec
-   [x] Dictionary codec
-   [x] Protocol codec
-   [x] Registry system
-   [x] Error handling
-   [x] Buffer management
-   [ ] Test suite
-   [ ] Performance benchmarking
-   [x] JAM Test Vectors
