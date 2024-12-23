# TsrCodec

Implementations for serializing and deserializing data types according to the JAM specs.

## Overview

The codec system provides:

-   Type-safe encoding and decoding of data structures
-   Support for primitive and composite types
-   Extensible registry for custom codec implementations
-   Automatic type inference and validation

## Usage

Basic usage:

```python
from jam.utils.codec import encode, decode, Array, Option, Vector, Tuple

# Simple types
encoded = encode(42) # Uses registered int codec
encoded = encode("hello") # Uses registered str codec

# Fixed arrays
numbers = Array[int, 5].encode([1, 2, 3, 4, 5])

# Optional values
maybe_int = Option[int].encode(42)
maybe_none = Option[int].encode(None)

# Dynamic vectors
numbers = Vector[int].encode([1, 2, 3])

# Tuples
point = Tuple[int, int].encode((10, 20))
```

## Data Types

| Type          | Description               | Format                           | Status |
| ------------- | ------------------------- | -------------------------------- | ------ |
| `bool`        | Boolean value             | `[0/1: u8]`                      | ✅     |
| `u8`          | 8-bit unsigned integer    | `[value: u8]`                    | ✅     |
| `u16`         | 16-bit unsigned integer   | `[value: u16]`                   | ✅     |
| `u32`         | 32-bit unsigned integer   | `[value: u32]`                   | ✅     |
| `u64`         | 64-bit unsigned integer   | `[value: u64]`                   | ✅     |
| `u128`        | 128-bit unsigned integer  | `[value: u128]`                  | ✅     |
| `u256`        | 256-bit unsigned integer  | `[value: u256]`                  | ✅     |
| `str`         | UTF-8 string              | `[length: vec_size][utf8_bytes]` | ✅     |
| `Array[T,N]`  | Fixed-length array        | `[item_0][item_1]...[item_N-1]`  | ⚠️     |
| `Option[T]`   | Optional value            | `[tag: u8][value if Some]`       | ⚠️     |
| `Vector[T]`   | Dynamic-length array      | `[length: vec_size][items...]`   | ⚠️     |
| `Tuple[T...]` | Fixed heterogeneous tuple | `[item_0][item_1]...`            | ⚠️     |
| `Dict[K,V]`   | Key-value mapping         | `[length: vec_size][pairs...]`   | ⚠️     |

### Vector Length Encoding

Vector lengths use a variable-length encoding scheme:

-   `0x00-0xFC`: Direct value (1 byte)
-   `0xFF`: u16 value (3 bytes)
-   `0xFE`: u24 value (4 bytes)
-   `0xFD`: u32 value (5 bytes)

## Protocol Specification

### Primitive Types

-   **Boolean**: Single byte, `0` for false, `1` for true
-   **Integers**: Little-endian encoded bytes
-   **Strings**: Length-prefixed UTF-8 bytes

### Composite Types

-   **Arrays**: Fixed length, concatenated elements
-   **Options**: 1-byte tag (`0` = None, `1` = Some) followed by value if present
-   **Vectors**: Length prefix followed by concatenated elements
-   **Tuples**: Concatenated elements in order
-   **Dictionaries**: Length prefix followed by sorted key-value pairs

### Type Safety

The codec system enforces:

-   Type checking during encoding/decoding
-   Buffer size validation
-   Value range constraints
-   Array length constraints

## Testing Status

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
-   [ ] JAM Test Vectors
