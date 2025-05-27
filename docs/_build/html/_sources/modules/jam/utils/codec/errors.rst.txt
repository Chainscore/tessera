jam.utils.codec.errors
==================

Error types for codec operations.

Exception Types
-------------

CodecError
^^^^^^^^
Base exception class for all codec-related errors:

.. code-block:: python

    class CodecError(Exception):
        pass

BufferError
^^^^^^^^^
Exception for buffer operation errors:

.. code-block:: python

    @dataclass
    class BufferError(CodecError):
        expected: int  # Expected bytes
        actual: int   # Available bytes
        message: str  # Error description

EncodeError
^^^^^^^^^
Exception raised during encoding:

.. code-block:: python

    class EncodeError(BufferError):
        pass

DecodeError
^^^^^^^^^
Exception raised during decoding:

.. code-block:: python

    class DecodeError(BufferError):
        pass

Common Error Cases
---------------

Buffer Operations
^^^^^^^^^^^^^^
1. Buffer underflow:
   
   .. code-block:: python
   
       if len(buffer) - offset < needed:
           raise BufferError(
               expected=needed,
               actual=len(buffer) - offset,
               message="Buffer too short"
           )

2. Buffer overflow:
   
   .. code-block:: python
   
       if offset + length > len(buffer):
           raise BufferError(
               expected=length,
               actual=len(buffer) - offset,
               message="Buffer overflow"
           )

Type Errors
^^^^^^^^^
1. Type mismatch:
   
   .. code-block:: python
   
       if not isinstance(value, expected_type):
           raise EncodeError(
               expected=sizeof(expected_type),
               actual=sizeof(type(value)),
               message=f"Expected {expected_type}, got {type(value)}"
           )

2. Invalid value:
   
   .. code-block:: python
   
       if value < 0 or value > max_value:
           raise EncodeError(
               expected=sizeof(int),
               actual=sizeof(value),
               message=f"Value {value} out of range"
           )

Format Errors
^^^^^^^^^^
1. Invalid UTF-8:
   
   .. code-block:: python
   
       try:
           return bytes.decode('utf-8')
       except UnicodeError as e:
           raise DecodeError(
               expected=len(bytes),
               actual=0,
               message=f"Invalid UTF-8: {e}"
           )

2. Invalid length prefix:
   
   .. code-block:: python
   
       if prefix > max_length:
           raise DecodeError(
               expected=max_length,
               actual=prefix,
               message="Invalid length prefix"
           )

Examples
-------

Basic Usage
^^^^^^^^^
.. code-block:: python

    try:
        codec.decode(buffer)
    except BufferError as e:
        print(f"Buffer error: expected {e.expected} bytes, got {e.actual}")
    except EncodeError as e:
        print(f"Encoding error: {e.message}")
    except DecodeError as e:
        print(f"Decoding error: {e.message}")

Custom Errors
^^^^^^^^^^
.. code-block:: python

    class ValidationError(CodecError):
        def __init__(self, field: str, value: Any):
            super().__init__(f"Invalid {field}: {value}")
            self.field = field
            self.value = value

    try:
        if value < 0:
            raise ValidationError("age", value)
    except ValidationError as e:
        print(f"Validation failed: {e.field} = {e.value}")

API Reference
-----------

.. automodule:: jam.utils.codec.errors
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
