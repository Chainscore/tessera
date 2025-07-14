from tsrkit_types.enum import Uint
from jam.types.protocol.crypto import Hash

a=[1,2,3]
integer=Uint(10)
key_hash = Hash.blake2b(integer.encode())

print(key_hash.hex(),",<-Hashed+++Original->",integer.encode().hex())
