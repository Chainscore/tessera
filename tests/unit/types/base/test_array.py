import pytest
from typing import List

from jam.types.base.array import Array
from jam.types.base.integers import U8
from jam.utils.codec.composite.arrays import ArrayCodec

def test_array_initialization():
    # Test empty initialization
    arr = Array(3)
    assert len(arr) == 3
    assert list(arr) == [None, None, None]

    # Test initialization with values
    arr = Array(3, [U8(1), U8(2), U8(3)])
    assert len(arr) == 3
    assert list(arr) == [U8(1), U8(2), U8(3)]

    # Test initialization with too many values
    with pytest.raises(ValueError):
        Array(2, [U8(1), U8(2), U8(3)])

def test_array_operations():
    arr = Array(4)
    
    # Test append
    arr.append(U8(1))
    assert list(arr) == [U8(1), None, None, None]
    
    arr.append(U8(2))
    assert list(arr) == [U8(1), U8(2), None, None]
    
    # Test append when full
    arr.append(U8(3))
    arr.append(U8(4))
    with pytest.raises(ValueError):
        arr.append(U8(5))

def test_array_insert():
    arr = Array(4, [U8(1), U8(2), U8(3)])
    
    # Test insert
    arr.insert(1, U8(5))
    assert list(arr) == [U8(1), U8(5), U8(2), U8(3)]
    
    # Test insert when full
    with pytest.raises(ValueError):
        arr.insert(0, U8(6))

def test_array_pop():
    arr = Array(4, [U8(1), U8(2), U8(3), U8(4)])
    
    # Test pop from end
    val = arr.pop()
    assert val == U8(4)
    assert list(arr) == [U8(1), U8(2), U8(3), None]
    
    # Test pop from index
    val = arr.pop(1)
    assert val == U8(2)
    assert list(arr) == [U8(1), U8(3), None, None]
    
    # Test pop with invalid index
    with pytest.raises(IndexError):
        arr.pop(10)

def test_array_remove():
    arr = Array(4, [U8(1), U8(2), U8(3), U8(4)])
    
    # Test remove existing value
    arr.remove(U8(2))
    assert list(arr) == [U8(1), U8(3), U8(4), None]
    
    # Test remove non-existent value
    with pytest.raises(ValueError):
        arr.remove(U8(10))

def test_array_indexing():
    arr = Array(4, [U8(1), U8(2), U8(3), U8(4)])
    
    # Test get item
    assert arr[0] == U8(1)
    assert arr[1:3] == [U8(2), U8(3)]
    
    # Test set item
    arr[0] = U8(5)
    assert arr[0] == U8(5)  
    
    # Test invalid index
    with pytest.raises(IndexError):
        arr[10] = U8(1)

def test_array_codec():
    arr = Array(4, [U8(1), U8(2), U8(3), U8(4)])
    
    # Test encoding
    buffer = bytearray(arr.encode_size())
    arr.encode_into(buffer)
    
    # Test decoding
    decoded, size = ArrayCodec.decode_from(4, U8, buffer)
    assert list(decoded) == list(arr)
    assert size == len(buffer)

def test_array_utilities():
    arr = Array(4, [U8(1), U8(2), U8(2), U8(3)])
    
    # Test count
    assert arr.count(U8(2)) == 2
    
    # Test index
    assert arr.index(U8(2)) == 1
    assert arr.index(U8(2), 2) == 2
    
    # Test clear
    arr.clear()
    assert list(arr) == [None, None, None, None]
    
    # Test reverse
    arr = Array(4, [U8(1), U8(2), U8(3), U8(4)])
    arr.reverse()
    assert list(arr) == [4, 3, 2, 1] 