
from jam.types.base.composite.option import Option
from jam.types.base.integers import U32


def test_option():
	# a = Option[U32] instance wrapping a U32
	a = Option[U32](U32(10))
	assert a is not None
	assert a.unwrap() == U32(10)
	assert a.is_some
	assert not a.is_none

	# None case
	b = Option[U32]()
	assert b.unwrap() is None
	assert b.is_none
	assert not b.is_some

def test_opt_codec():
	a = Option[U32](U32(10))
	enc_a = a.encode()
	assert len(enc_a) == 4+1

	dec_a = a.decode(enc_a)
	assert dec_a == a

	n = Option[U32](None)
	enc_n = n.encode()
	assert len(enc_n) == 1

	dec_n = n.decode(enc_n)
	assert dec_n == n