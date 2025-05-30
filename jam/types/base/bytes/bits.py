from typing import ClassVar
from jam.utils.codec.composite import BitSequenceCodec
from ..sequences.base import Vector, Seq


class Bits(Seq):
	"""Bits[size, order]"""
	_element_type = bool,int
	_min_length: ClassVar[int] = 0
	_max_length: ClassVar[int] = 2 ** 64

	def __class_getitem__(cls, params):
		min_l, max_l, _bo = 0, 2**64, "msb"
		if isinstance(params, tuple):
			min_l, max_l, _bo = params[0], params[0], params[1]
		else:
			if isinstance(params, int):
				min_l, max_l = params, params
			else:
				_bo = params

		codec = BitSequenceCodec[(max_l, _bo) if (min_l == max_l) else _bo]()
		return type(cls.__class__.__name__, (cls,), {"_min_length": min_l, "_max_length": max_l, "_order": _bo, "codec": codec})