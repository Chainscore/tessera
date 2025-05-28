from .bytes import Bytes, BitVector

# TODO - upon Vector implementation
# Initially thought this could be an extension of Bytes, but since byte always paired
# with 8 bits - tracking actual length of the bitarray would get tricky
class Bits(): ...