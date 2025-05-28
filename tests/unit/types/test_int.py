from dataclasses import dataclass

from jam.types.base import U8, Int, U16


def test_int_type():
	a = U8(28)
	assert a

def test_int_decodable():
	a = U8.decode_from(b'08')[0]
	assert a > 0

def test_int_encode():
	a = U8(100)
	encoded = a.encode()
	assert a == U8.decode_from(encoded)[0]

def test_int_instance():
	assert isinstance(U8(10), U8)
	assert isinstance(U8(10), int)
	assert not isinstance(U8(10), U16)

def test_int_compare():
	assert U8(10) == U16(10)
	assert type(U8(10)) != type(U16(10))

def test_gen_int_type():
	a = Int(1000)
	assert a

def test_gen_int_decodable():
	a = Int.decode_from(b'08')[0]
	assert a > 0

def test_gen_int_encode():
	a = Int(100)
	encoded = a.encode()
	assert a == Int.decode_from(encoded)[0]

def test_static_type_checker():
	@dataclass
	class DataStore:
		a: U8
		b: U16

	# Shows error
	DataStore(a=19, b=288)
	DataStore(a=U16(19), b=U8(288))
	# This is fine
	DataStore(a=U8(19), b=U16(288))

