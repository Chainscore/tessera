from jam.types.base.bytes import Bytes
from jam.types.base.bytes.bits import Bits


def test_bytes_init():
	a = Bytes(b"hello")
	assert a
	assert isinstance(a, Bytes)

def test_bytes_from_bits():
	a = Bytes.from_bits([True, False, True, False, False, False, False, False])
	assert a.hex() == "a0"
	# lsb
	a = Bytes.from_bits([True, False, True, False, False, False, False, False], "lsb")
	assert a.hex() == "05"

def test_var_bytes_enc():
	a = Bytes(b"hello")
	enc = a.encode()
	assert a == Bytes.decode_from(enc)[0]

def test_ba32_enc():
	a = Bytes[32](bytes(32))
	enc = a.encode()
	assert a == Bytes[32].decode_from(enc)[0]

def test_bitarr_init():
	a = Bits([1, 0, 1, 0])
	assert len(a) == 4

def test_bitarr_enc():
	a = Bits[4]([1, 0, 1, 0])
	assert a.encode().hex() == "a0"

	b = Bits[4, "lsb"]([1, 0, 1, 0])
	assert b.encode().hex() == "05"

	b = Bits["lsb"]([1, 0, 1, 0])
	assert b.encode().hex() == "0405"
	assert b.encode()[0] == 4