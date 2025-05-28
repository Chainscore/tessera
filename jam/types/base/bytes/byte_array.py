from jam.types.base import Bytes


class ByteArray32(Bytes):
	_length = 32

class ByteArray64(Bytes):
	_length = 64

class ByteArray96(Bytes):
	_length = 96

class ByteArray144(Bytes):
	_length = 144

class ByteArray784(Bytes):
	_length = 784

# Note - feel free to add more as needed