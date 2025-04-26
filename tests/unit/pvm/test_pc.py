from jam.pvm.code import Code
from jam.pvm.status import HALT
from jam.types.protocol.core import Gas

fib_instructions = [0,0,39,54,7,0,0,255,254,51,8,1,51,9,1,40,3,0,149,119,255,81,7,12,100,138,200,152,8,100,169,40,243,100,135,51,8,51,9,1,50,0,65,210,164,84,53]
args = int(10).to_bytes()

def test_en_decode():
    p = Code(b"", b"", bytes(fib_instructions), 0, 0, args)
    bytecode = p.encode()
    print(f"\n\nFibonacci fn bytecode: 0x{bytecode.hex()} \n")
    p_decoded = Code.decode_from(bytecode)
    assert p == p_decoded

def test_program():
    p = Code(b"", b"", bytes(fib_instructions), 0, 0, args)
    result = p.execute(gas=Gas(100000))
    assert result[0] == HALT
    print(f"\n\nFibonacci sequence of size {int.from_bytes(args)}: [-1, -2] = {result[3][7], result[3][10]} \n")