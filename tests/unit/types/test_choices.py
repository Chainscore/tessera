
from jam.types.base.composite.option import Option
from jam.types.base.integers import U32


def test_option():
	# a = Option[U32] instance wrapping a U32
	a = Option[U32](U32(10))
	assert a is not None
	assert a.unwrap() == U32(10)

	# None case
	b = Option[U32]()
	assert not b
	assert b.unwrap() is None
	assert b.is_none

def test_opt_codec():
	a = Option[U32](U32(10))
	enc_a = a.encode()
	assert len(enc_a) == 4+1

	dec_a = a.decode(enc_a)
	print(dec_a)