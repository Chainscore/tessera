import math
from jam.utils.codec.primitives.integers import IntegerCodec


class InstructionMapper:
    """Maps instruction opcodes to their respective functions and groups."""

    # Grouped instructions mapped to functions
    INSTRUCTION_GROUPS = {
        "none": {
            0: "trap",
            1: "fallthrough",
        },
        "reg_imm": {
            50: "jump_ind",
            51: "load_imm",
            52: "load_u8",
            53: "load_i8",
            54: "load_u16",
            55: "load_i16",
            56: "load_u32",
            57: "load_i32",
            58: "load_u64",
            59: "store_u8",
            60: "store_u16",
            61: "store_u32",
            62: "store_u64",
        },
        "reg_imm_imm": {
            70: " store_imm_ind_u8",
            71: " store_imm_ind_u16",
            72: " store_imm_ind_u32",
            73: " store_imm_ind_u64"
        },
        "reg_imm_offset": {
            80: "load_imm_and_jump",
            81: "branch_eq_imm",
            82: "branch_not_eq_imm",
            83: "branch_le_u_imm",
            84: "branch_le_or_equal_u_imm",
            85: "branch_gt_or_equal_u_imm",
            86: "branch_gt_u_imm",
            87: "branch_le_signed_imm",
            88: "branch_le_or_equal_signed_imm",
            89: "branch_gt_or_equal_signed_imm",
            90: "branch_gt_signed_imm",
        },
        "offset": {
            40: "jump",
        },
        "imm": {
            10: "ecalli",
        },
        "imm_imm": {
            30: "store_imm_u8",
            31: "store_imm_u16",
            32: "store_imm_u32",
            33: "store_imm_u64",
        },
        "reg_reg": {
            100: "move_reg",
            101: "sbrk",
            102: "count_set_bits_64",
            103: "count_set_bits_32",
            104: "count_leading_zero_bits_64",
            105: "count_leading_zero_bits_32",
            106: "count_trailing_zero_bits_64",
            107: "count_trailing_zero_bits_32",
            108: "sign_extend_8",
            109: "sign_extend_16",
            110: "zero_extend_16",
            111: "reverse_byte",
        },
        # Group reg_reg_imm
        "reg_reg_imm": {
           120: "store_ind_u8",
           121: "store_ind_u16",
           122: "store_ind_u32",
           123: "store_ind_u64",
           124: "load_ind_u8",
           125: "load_ind_i8",
           126: "load_ind_u16",
           127: "load_ind_i16",
           129: "load_ind_i32",
           128: "load_ind_u32",
           130: "load_ind_u64",
           131: "add_imm_32",
           149: "add_imm_64",
           132: "and_imm",
           133: "xor_imm",
           134: "or_imm",
           135: "mul_imm_32",
           150: "mul_imm_64",
           136: "set_lt_unsigned_imm",
           137: "set_lt_signed_imm",
           138: "shlo_l_imm_32",
           151: "shlo_l_imm_64",
           139: " shlo_r_imm_32",
           152: " shlo_r_imm_64",
           140: " shar_r_imm_32",
           153: " shar_r_imm_64",
           141: "neg_add_imm_32",
           154: "neg_add_imm_64",
           142: "set_gt_unsigned_imm",
           143: "set_gt_signed_imm",
           145: " shlo_r_imm_alt_32",
           156: " shlo_r_imm_alt_64",
           146: " shar_r_imm_alt_32",
           157: " shar_r_imm_alt_64",
           144: "shlo_l_imm_alt_32",
           155: "shlo_l_imm_alt_64",
           147: "cmov_iz_imm",
           148: "cmov_nz_imm",
           160: "rot_r_imm_32",
           161: "rot_r_imm_alt_32",
           158: "rot_r_imm_64",
           159: "rot_r_imm_alt_64",
        },
        "reg_reg_off": {
            170: "branch_eq",
            171: "branch_ne",
            172: "branch_lt_u",
            173: "branch_lt_s",
            174: "branch_ge_u",
            175: "branch_ge_s",
        },
        "reg_reg_imm_imm": {
            180: "load_imm_and_jump_ind",
        },
        "reg_imm64": {
            20: "load_imm_64",
        },
        "reg_reg_reg": {
            190: "add_32",
            191: "sub_32",
            192: "mul_32",
            193: "div_u_32",
            194: "div_signed_32",
            195: "rem_u_32",
            196: "rem_signed_32",
            197: "shlo_l_32",
            198: " shlo_r_32",
            199: " shar_r_32",
            200: "add_64",
            201: "sub_64",
            202: "mul_64",
            203: "div_u_64",
            204: "div_signed_64",
            205: "rem_u_64",
            206: "rem_signed_64",
            207: "shlo_l_64",
            208: " shlo_r_64",
            209: " shar_r_64",
            210: "_and",
            211: "_xor",
            212: "_or",
            213: "mul_upper_signed_signed",
            214: "mul_upper_u_u",
            215: "mul_upper_signed_u",
            216: "set_le_than_u",
            217: "set_le_than_signed",
            218: "cmov_iz",
            219: "cmov_nz",
            220: "rotate_left_64",
            221: "rotate_left_32",
            222: "rot_r_64",
            223: "rot_r_32",
            224: "and_inverted",
            225: "or_inverted",
            226: "_xnor",
            227: "_max",
            228: "max_u",
            229: "_min",
            230: "min_u",
        },
    }

    @classmethod
    def get_instruction(cls, opcode: int):
        """
        Returns the instruction group and function name for a given opcode.

        :param opcode: Opcode to look up.
        :return: (group_name, function_name)
        """
        for group_name, instructions in cls.INSTRUCTION_GROUPS.items():
            if opcode in instructions:
                function_name = instructions[opcode]
                return group_name, globals()[function_name]
        return opcode, None

    @classmethod
    def execute(cls, opcode: int, *args):
        """
        Executes the function associated with the given opcode.

        :param opcode: Opcode to execute.
        :param args: Arguments required by the function.
        """
        group, function = cls.get_instruction(opcode)
        if function is None:
            print(f"Opcode {opcode} is unknown.")
            return

        # Call the function
        function(*args)


def signed_ext(num, n):
    return num + (math.floor(num/2**(8*n-1)))*(2**64-2**(8*n))


def reg_value(instance, r):
    return instance.initial_regs[r]


def signed_z(num, n):
    if num < 2**(8*n-1):
        return num
    else:
        return num - 2 ** (8*n)


def branch(instance, b, c):
    if not c:
        return
    elif b > len(instance.program.instruction_set):
        return "fault"
    else:
        return b


def djump(instance, a, i):
    j = instance.program.jump_table
    if a == 2**32 - 2**16:
        return {"continue", i}
    elif a == 0 or a > len(j*2) or a % 2 != 0 or j[a/2-1] > len(instance.program.instruction_set):
        return {"fault", i}
    else:
        return {"continue", j[a/2-1]}


def inverse_signed_z(num, n):
    return (2**(8*n) + num) % 2**(8*n)


def seq_b(num, n):
    seq = [(num >> i) & 1 for i in range(8 * n)]
    return ''.join(map(str, [(num >> i) & 1 for i in range(8 * n)]))


def valid_address(initial_page_map, address, writable=None):
    for region in initial_page_map:
        start = region["address"]
        end = start + region["length"]

        if start <= address < end:
            if writable is None or region.get("is-writable", False) == writable:
                return start
    return False


def memory_value(memory_array, start_index, end_index=None):
    for region in memory_array:
        start_address = region["address"]
        contents = region["contents"]
        end_address = start_address + len(contents)

        if end_index is None:  # Single index case
            if start_address <= start_index < end_address:
                return contents[start_index - start_address]

        else:  # Range case
            if start_address <= start_index < end_address and start_address <= end_index < end_address:
                return contents[start_index - start_address: end_index - start_address + 1]

    return None  # If the index or range is not found


def store_value(initial_memory, address, value):
    for region in initial_memory:
        start_address = region["address"]
        contents = region["contents"]
        end_address = start_address + len(contents)

        if start_address <= address < end_address:
            # Update the existing value at the given address
            contents[address - start_address] = value if isinstance(value, int) else value[0]
            return initial_memory

    # If address not found, create a new memory object and append it
    obj = {
        "address": address,
        "contents": [value] if isinstance(value, int) else value
    }
    initial_memory.append(obj)
    return initial_memory


def max_n_where_sum_is_zero(omega_a_values, n_limit=2 ** 65):
    """
    Computes the maximum n such that the sum of all bits across B_8(omega_A) from i=0 to i<n is zero.
    Parameters:
    - omega_A_values: List of integers representing omega_A values.
    - n_limit: Upper bound for n (default: 2^65).
    Returns:
    - Maximum n where sum(B_8(omega_A)_i) = 0.
    """
    bit_length = 8  # Each omega_A is represented in 8-bit form
    bit_sums = [0] * bit_length  # Track sums for each bit position

    max_n = 0  # The largest n where sum remains 0

    for n, omega_A in enumerate(omega_a_values):
        if n >= n_limit:  # Ensure we do not exceed the limit
            break

        binary_rep = format(omega_A, f'0{8*1}b')  # Convert omega_A to an 8-bit binary string

        # Accumulate bitwise sums for each bit position
        for i in range(bit_length):
            bit_sums[i] += int(binary_rep[i])  # Convert bit to int and sum

        # If all bit_sums remain 0, update max_n; otherwise, break
        if all(bit == 0 for bit in bit_sums):
            max_n = n + 1
        else:
            break  # Stop at the first instance where sum is nonzero

    return max_n


def binary_operation(bin_str1, bin_str2, operation):
    """
    Perform a bitwise operation (AND, OR, XOR) on two binary strings of equal length.
    :param bin_str1: First binary string.
    :param bin_str2: Second binary string.
    :param operation: Operation type - 'AND', 'OR', 'XOR'.
    :return: Resultant binary string after applying the operation.
    """
    if len(bin_str1) != len(bin_str2):
        raise ValueError("Both binary strings must be of equal length")

    if operation == 'AND':
        result = ''.join(str(int(a) & int(b)) for a, b in zip(bin_str1, bin_str2))
    elif operation == 'OR':
        result = ''.join(str(int(a) | int(b)) for a, b in zip(bin_str1, bin_str2))
    elif operation == 'XOR':
        result = ''.join(str(int(a) ^ int(b)) for a, b in zip(bin_str1, bin_str2))
    else:
        raise ValueError("Invalid operation. Choose 'AND', 'OR', or 'XOR'.")

    return result


def binary_not(bin_str1):
    return ''.join(str(~int(a)) for a in zip(bin_str1))


def inverse_seq_b(binary_str):
    """
    Converts a binary string representation back to its integer form.
    :param binary_str: Binary string (e.g., "1101").
    :return: Integer representation of the binary sequence.
    """
    total_sum = 0  # Initialize sum to 0

    for i, bit in enumerate(binary_str):
        weighted_value = int(bit) * (2 ** i)  # Convert char to int and apply the same logic
        total_sum += weighted_value  # Add to total sum

    return total_sum  # Return the computed integer


def reg_reg(arg):
    print("helo")
    reg_a = min(arg[0] % 16, 12)
    reg_d = min(math.floor(arg[0] / 16), 12)
    return int(reg_a), int(reg_d)


def reg_reg_imm(arg):
    reg_a = min(12, arg[0] % 16)
    reg_b = min(12, math.floor(arg[0] / 16))
    l_x = min(4, max(0, len(arg)-1))
    v_x = IntegerCodec.decode_from(l_x, arg[1:l_x+1])
    return int(reg_a), int(reg_b), l_x, v_x[0]


def reg_imm_imm(instance, arg):
    ln = len(arg)
    reg_a = int(min(12, arg[0] % 16))
    l_x = min(4, (math.floor(arg[0])/16) % 16)
    l_y = min(4, max(0, ln - l_x - 1))
    v_x = signed_ext(IntegerCodec.decode_from(l_x, arg[1, l_x+1])[0], l_x)
    v_y = signed_ext(IntegerCodec.decode_from(l_y, arg[l_x+1:l_x+l_y+1])[0], l_y)
    return reg_a, l_x, l_y, v_x, v_y


def reg_imm(arg):
    reg_a = min(12, arg[0] % 16)
    l_x = min(4, max(0, len(arg) - 1))
    v_x = IntegerCodec.decode_from(l_x, arg[1:l_x+1])
    return int(reg_a), l_x, v_x[0]


def reg_ext_imm(arg):
    reg_a = min(12, arg[0] % 16)
    v_x = IntegerCodec.decode_from(8, arg[1:9])
    return int(reg_a), v_x[0]


def imm_imm(arg):
    ln = len(arg)
    l_x = int(min(4, arg[0] % 8))
    l_y = min(4, max(0, (ln - l_x - 1)))
    v_x = signed_ext(IntegerCodec.decode_from(l_x, arg[1:l_x + 1])[0], l_x)
    v_y = signed_ext(IntegerCodec.decode_from(l_y, arg[l_x + 1:l_x + l_y + 1])[0], l_y)
    return l_x, l_y, v_x, v_y


def count_set_bits(binary_str: str) -> int:
    if not all(c in '01' for c in binary_str):
        raise ValueError("Input is not a valid binary string.")

    return binary_str.count('1')


def reg_reg_reg(arg):
    reg_a = min(arg[0] % 16, 12)
    reg_b = min(math.floor(arg[0] / 16), 12)
    reg_d = min(12, arg[1])
    return int(reg_a), int(reg_b), int(reg_d)
# Define all instruction functions


def trap(instance, arg):
    print("trap")


def fallthrough(instance, arg):
    print("fallthrough")


def jump_ind(instance, arg):
    print(f"jump_ind ")


def load_imm(instance, arg):
    print(f"load_imm ")
    reg_a, l_a, v_x = reg_imm(arg)
    instance.initial_regs[reg_a] = v_x


def load_u8(instance, arg):
    print(f"load_u8 ")
    reg_a, l_a, v_x = reg_imm(arg)
    u_vx = memory_value(instance.initial_memory, v_x)
    instance.initial_regs[reg_a] = u_vx


def load_i8(instance, arg):
    print(f"load_i8 ")
    reg_a, l_a, v_x = reg_imm(arg)
    u_vx = memory_value(instance.initial_memory, v_x)
    instance.initial_regs[reg_a] = signed_ext(u_vx, 1)


def load_u16(instance, arg):
    print(f"load_u16 ")
    reg_a, l_a, v_x = reg_imm(arg)
    u_vx = memory_value(instance.initial_memory, v_x, 2)
    instance.initial_regs[reg_a] = IntegerCodec.decode_from(2, u_vx)[0]


def load_i16(instance, arg):
    print(f"load_i16 ")
    reg_a, l_a, v_x = reg_imm(arg)
    u_vx = memory_value(instance.initial_memory, v_x, 2)
    instance.initial_regs[reg_a] = signed_ext(IntegerCodec.decode_from(2, u_vx)[0], 2)


def load_u32(instance, arg):
    print(f"load_u32 ")
    reg_a, l_a, v_x = reg_imm(arg)
    u_vx = memory_value(instance.initial_memory, v_x, 4)
    instance.initial_regs[reg_a] = IntegerCodec.decode_from(4, u_vx)[0]


def load_i32(instance, arg):
    print(f"load_i32 ")
    reg_a, l_a, v_x = reg_imm(arg)
    u_vx = memory_value(instance.initial_memory, v_x, 4)
    instance.initial_regs[reg_a] = signed_ext(IntegerCodec.decode_from(4, u_vx)[0], 4)


def load_u64(instance, arg):
    print(f"load_u64")
    reg_a, l_a, v_x = reg_imm(arg)
    u_vx = memory_value(instance.initial_memory, v_x, 8)
    instance.initial_regs[reg_a] = IntegerCodec.decode_from(8, u_vx)[0]


def store_u8(instance, arg):
    print(f"store_u8 ")
    reg_a, l_a, v_x = reg_imm(arg)
    w_a = reg_value(instance, reg_a)
    address = v_x
    contents = [w_a % 2**8]
    print(valid_address(instance.initial_page_map, address))
    if valid_address(instance.initial_page_map, address):
        instance.initial_memory = store_value(instance.initial_memory, address, contents)


def store_u16(instance, arg):
    print(f"store_u16 ")
    reg_a, l_a, v_x = reg_imm(arg)
    w_a = reg_value(instance, reg_a)
    address = v_x
    serialize = IntegerCodec(2)
    buffer = bytearray(2)
    IntegerCodec.encode_into(serialize, w_a % 2**16, buffer)
    contents = list(buffer.rstrip(b'\x00'))
    print(valid_address(instance.initial_page_map, address))
    if valid_address(instance.initial_page_map, address):
        instance.initial_memory = store_value(instance.initial_memory, address, contents)


def store_u32(instance, arg):
    print(f"store_u32 ")
    reg_a, l_a, v_x = reg_imm(arg)
    w_a = reg_value(instance, reg_a)
    address = v_x
    serialize = IntegerCodec(4)
    buffer = bytearray(4)
    IntegerCodec.encode_into(serialize, w_a % 2 ** 32, buffer)
    contents = list(buffer.rstrip(b'\x00'))
    print(valid_address(instance.initial_page_map, address))
    if valid_address(instance.initial_page_map, address):
        instance.initial_memory = store_value(instance.initial_memory, address, contents)


def store_u64(instance, arg):
    print(f"store_u64 ")
    reg_a, l_a, v_x = reg_imm(arg)
    w_a = reg_value(instance, reg_a)
    address = v_x
    serialize = IntegerCodec(8)
    buffer = bytearray(8)
    IntegerCodec.encode_into(serialize, w_a, buffer)
    contents = list(buffer.rstrip(b'\x00'))
    print(valid_address(instance.initial_page_map, address))
    if valid_address(instance.initial_page_map, address):
        instance.initial_memory = store_value(instance.initial_memory, address, contents)


def load_imm_and_jump(instance, arg):
    print(f"load_imm_and_jump ")


def branch_eq_imm(instance, arg):
    print(f"branch_eq_imm ")


def branch_not_eq_imm(instance, arg):
    print(f"branch_not_eq_imm ")


def branch_le_u_imm(instance, arg):
    print(f"branch_le_u_imm ")


def branch_le_or_equal_u_imm(instance, arg):
    print(f"branch_le_or_equal_u_imm ")


def branch_gt_or_equal_u_imm(instance, arg):
    print(f"branch_gt_or_equal_u_imm ")


def branch_gt_u_imm(instance, arg):
    print(f"branch_gt_u_imm ")


def branch_le_signed_imm(instance, arg):
    print(f"branch_le_signed_imm ")


def branch_le_or_equal_signed_imm(instance, arg):
    print(f"branch_le_or_equal_signed_imm ")


def branch_gt_or_equal_signed_imm(instance, arg):
    print(f"branch_gt_or_equal_signed_imm ")


def branch_gt_signed_imm(instance, arg):
    print(f"branch_gt_signed_imm ")


def jump(instance, arg):
    print(f"jump ")


def ecalli(instance, arg):
    print(f"ecalli ")


def store_imm_u8(instance, arg):
    print(f"store_imm_u8 ")
    l_x, l_y, v_x, v_y = imm_imm(arg)
    if valid_address(instance.initial_page_map, v_x, writable=True):
        instance.initial_memory = store_value(instance.initial_memory, v_x, [v_y % 2**8])


def store_imm_u16(instance, arg):
    print(f"store_imm_u16 ")
    l_x, l_y, v_x, v_y = imm_imm(arg)
    serialize = IntegerCodec(2)
    buffer = bytearray(2)
    IntegerCodec.encode_into(serialize, v_y % 2**16, buffer)
    address = valid_address(instance.initial_page_map, v_x, writable=True)
    if address:
        instance.initial_memory = store_value(instance.initial_memory, v_x, list(buffer.rstrip(b'\x00')))


def store_imm_u32(instance, arg):
    print(f"store_imm_u32 instance, arg")
    l_x, l_y, v_x, v_y = imm_imm(arg)
    serialize = IntegerCodec(4)
    buffer = bytearray(4)
    IntegerCodec.encode_into(serialize, v_y % 2**32, buffer)
    address = valid_address(instance.initial_page_map, v_x, writable=True)
    if address:
        instance.initial_memory = store_value(instance.initial_memory, v_x, list(buffer.rstrip(b'\x00')))


def store_imm_u64(instance, arg):
    print(f"store_imm_u64 ")
    l_x, l_y, v_x, v_y = imm_imm(arg)
    serialize = IntegerCodec(8)
    buffer = bytearray(8)
    IntegerCodec.encode_into(serialize, v_y, buffer)
    address = valid_address(instance.initial_page_map, v_x, writable=True)
    if address:
        instance.initial_memory = store_value(instance.initial_memory, v_x, list(buffer.rstrip(b'\x00')))


def move_reg(instance, arg):
    print(f"move_reg ")
    reg_a, reg_d = reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    instance.initial_regs[reg_d] = w_a


def sbrk(instance, arg):
    print("sbrk")


def count_set_bits_64(instance, arg):
    print("count_set_bits_64")
    reg_a, reg_d = reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    instance.initial_regs[reg_d] = count_set_bits(seq_b(w_a, 8))


def count_set_bits_32(instance, arg):
    print("count_set_bits_32")
    reg_a, reg_d = reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    instance.initial_regs[reg_d] = count_set_bits(seq_b(w_a % 2**32, 4))

# Define all remaining instruction functions


def count_leading_zero_bits_32(instance, arg):
    print("count_leading_zero_bits_32")


def count_trailing_zero_bits_64(instance, arg):
    print("count_trailing_zero_bits_64")


def count_trailing_zero_bits_32(instance, arg):
    print("count_trailing_zero_bits_32")


def sign_extend_8(instance, arg):
    print("sign_extend_8")
    reg_a, reg_d = reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    instance.initial_regs[reg_d] = inverse_signed_z(signed_z(w_a % 2**8, 1), 8)


def sign_extend_16(instance, arg):
    print("sign_extend_16")
    reg_a, reg_d = reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    instance.initial_regs[reg_d] = inverse_signed_z(signed_z(w_a % 2 ** 16, 2), 8)


def zero_extend_16(instance, arg):
    print("zero_extend_16")
    reg_a, reg_d = reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    instance.initial_regs[reg_d] = w_a % 2**16


def reverse_byte(instance, arg):
    print("reverse_byte")


def load_imm_and_jump_ind(instance, arg):
    print(f"load_imm_and_jump_ind ")


def load_imm_64(instance, arg):
    print(f"load_imm_64 ")
    reg_a, v_x = reg_ext_imm(arg)
    instance.initial_regs[reg_a] = v_x


def add_32(instance, arg):
    print("add_32")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    instance.initial_regs[reg_d] = signed_ext((instance.initial_regs[reg_a] + instance.initial_regs[reg_b]) % 2**32, 4)
    print(f"computed regs:{reg_value(instance, reg_d)}")


def sub_32(instance, arg):
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    instance.initial_regs[reg_d] = signed_ext((instance.initial_regs[reg_a] + 2**32 - (instance.initial_regs[reg_b] % 2**32)), 4)
    print(f"sub_32 ")


def mul_32(instance, arg):
    print(f"mul_32 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    instance.initial_regs[reg_d] = signed_ext((instance.initial_regs[reg_a]*instance.initial_regs[reg_b]) % 2**32, 4)


def div_u_32(instance, arg):
    print(f"div_u_32 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    if instance.initial_regs[reg_b] % 2**32 == 0:
        instance.initial_regs[reg_d] = 2**64 - 1
    else:
        instance.initial_regs[reg_d] = math.floor((instance.initial_regs[reg_a] % 2**32)/(instance.initial_regs[reg_b] % 2**32))


def div_signed_32(instance, arg):
    print(f"div_signed_32 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    a = signed_z(instance.initial_regs[reg_a] % 2**32, 4)
    b = signed_z(instance.initial_regs[reg_b] % 2**32, 4)
    if b == 0:
        instance.initial_regs[reg_d] = 2**64 - 1
    elif a == -2**31 and b == -1:
        instance.initial_regs[reg_d] = a
    else:
        instance.initial_regs[reg_d] = inverse_signed_z(math.floor(a/b), 8)


def rem_u_32(instance, arg):
    print(f"rem_u_32 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    if instance.initial_regs[reg_b] % 2**32 == 0:
        instance.initial_regs[reg_d] = signed_ext((instance.initial_regs[reg_b] % 2**32) % (instance.initial_regs[reg_a] % 2**32), 4)


def rem_signed_32(instance, arg):
    print(f"rem_signed_32 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    a = signed_z(reg_value(instance, reg_a) % 2**32, 4)
    b = signed_z(reg_value(instance, reg_b) % 2**32, 4)
    if b == 0:
        instance.initial_regs[reg_d] = inverse_signed_z(a, 8)
    elif a == -2**31 and b == -1:
        instance.initial_regs[reg_d] = 0
    else:
        instance.initial_regs[reg_d] = inverse_signed_z(a % b, 8)


def shlo_l_32(instance, arg):
    print(f"shlo_l_32 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    instance.initial_regs[reg_d] = signed_ext((reg_value(instance, reg_a) * 2**(reg_value(instance, reg_b) % 32)) % 2**32, 4)


def  shlo_r_32(instance, arg):
    print(f" shlo_r_32 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    instance.initial_regs[reg_d] = signed_ext(math.floor((instance.initial_regs[reg_a] % 2**32) / 2**(instance.initial_regs[reg_b] % 32)), 4)


def  shar_r_32(instance, arg):
    print(f" shar_r_32 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    instance.initial_regs[reg_d] = inverse_signed_z(math.floor(signed_z(instance.initial_regs[reg_a] % 2**32, 4) / 2**(instance.initial_regs[reg_b] % 32)), 8)


def add_64(instance, arg):
    print(f"add_64 ")
    reg1 = min(arg[0] % 16, 12)
    reg2 = min(math.floor(arg[0] / 16), 12)
    reg3 = min(12, arg[1])
    instance.initial_regs[int(reg3)] = signed_ext((instance.initial_regs[int(reg1)] + instance.initial_regs[int(reg2)]) % 2 ** 64, 4)
    print(f"computed regs:{instance.initial_regs[int(reg3)]}")


def sub_64(instance, arg):
    print(f"sub_64 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    instance.initial_regs[reg_d] = (instance.initial_regs[reg_a] + 2**64 - instance.initial_regs[reg_b]) % 2**64


def mul_64(instance, arg):
    print(f"mul_64 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    instance.initial_regs[reg_d] = (instance.initial_regs[reg_a] * instance.initial_regs[reg_b]) % 2**64


def div_u_64(instance, arg):
    print(f"div_u_64 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    if instance.initial_regs[reg_b] == 0:
        instance.initial_regs[reg_d] = 2**64 - 1
    else:
        instance.initial_regs[reg_d] = math.floor(instance.initial_regs[reg_a]/instance.initial_regs[reg_b])


def div_signed_64(instance, arg):
    print(f"div_signed_64 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    a = signed_z(instance.initial_regs[reg_a], 8)
    b = signed_z(instance.initial_regs[reg_b], 8)
    if instance.initial_regs[reg_b] == 0:
        instance.initial_regs[reg_d] = 2**64 - 1
    elif a== -2**63 and b == -1:
        instance.initial_regs[reg_d] = instance.initial_regs[reg_a]
    else:
        instance.initial_regs[reg_d] = inverse_signed_z(math.floor(a / b), 8)


def rem_u_64(instance, arg):
    print(f"rem_u_64 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    if instance.initial_regs[reg_b] == 0:
        instance.initial_regs[reg_d] = instance.initial_regs[reg_a]
    else:
        instance.initial_regs[reg_d] = instance.initial_regs[reg_a] % instance.initial_regs[reg_b]


def rem_signed_64(instance, arg):
    print(f"rem_signed_64 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    a = signed_z(instance.initial_regs[reg_a], 8)
    b = signed_z(instance.initial_regs[reg_b], 8)
    if instance.initial_regs[reg_b] == 0:
        instance.initial_regs[reg_d] = instance.initial_regs[reg_a]
    elif a == -2**63 and b == -1:
        instance.initial_regs[reg_d] = 0
    else:
        inverse_signed_z(a % b, 8)


def shlo_l_64(instance, arg):
    print(f"shlo_l_64 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    a = 2**(instance.initial_regs[reg_b] % 64)
    instance.initial_regs[reg_d] = (instance.initial_regs[reg_a] * a) % 2**64


def  shlo_r_64(instance, arg):
    print(f" shlo_r_64 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    a = 2 ** (instance.initial_regs[reg_b] % 64)
    instance.initial_regs[reg_d] = math.floor(instance.initial_regs[reg_a] / a)


def  shar_r_64(instance, arg):
    print(f" shar_r_64 ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    a = signed_z(w_a, 8)
    b = 2**(w_b % 64)
    instance.initial_regs[reg_d] = inverse_signed_z(math.floor(a / b), 8)


def _and(instance, arg):
    print(f"and ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    a = seq_b(w_b, 8)
    b = seq_b(w_a, 8)
    temp = binary_operation(a, b, "AND")
    instance.initial_regs[reg_d] = inverse_seq_b(temp)


def _xor(instance, arg):
    print(f"_xor ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    a = seq_b(w_b, 8)
    b = seq_b(w_a, 8)
    temp = binary_operation(a, b, "XOR")
    instance.initial_regs[reg_d] = inverse_seq_b(temp)


def _or(instance, arg):
    print(f"_or")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    a = seq_b(w_b, 8)
    b = seq_b(w_a, 8)
    temp = binary_operation(a, b, "OR")
    instance.initial_regs[reg_d] = inverse_seq_b(temp)


def mul_upper_signed_signed(instance, arg):
    print(f"mul_upper_signed_signed ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    a = signed_z(w_a, 8)
    b = signed_z(w_b, 8)
    instance.initial_regs[reg_d] = inverse_signed_z(math.floor((a*b) / 2**64), 8)


def mul_upper_u_u(instance, arg):
    print(f"mul_upper_u_u ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    instance.initial_regs[reg_d] = math.floor((w_a*w_b) / 2**64)


def mul_upper_signed_u(instance, arg):
    print(f"mul_upper_signed_u")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    a = signed_z(w_a, 8)
    instance.initial_regs[reg_d] = inverse_signed_z(math.floor((a * w_b) / 2**64), 8)


def set_le_than_u(instance, arg):
    print(f"set_le_than_u ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    instance.initial_regs[reg_d] = w_a < w_b


def set_le_than_signed(instance, arg):
    print(f"set_le_than_signed")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    a = signed_z(w_a, 8)
    b = signed_z(w_b, 8)
    instance.initial_regs[reg_d] = a < b


def cmov_iz(instance, arg):
    print(f"cmov_iz")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    if w_b == 0:
        instance.initial_regs[reg_d] = w_a
    else:
        instance.initial_regs[reg_d] = instance.initial_regs[reg_d]


def cmov_nz(instance, arg):
    print(f"cmov_nz")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    if w_b != 0:
        instance.initial_regs[reg_d] = w_a
    else:
        instance.initial_regs[reg_d] = instance.initial_regs[reg_d]


def rotate_left_64(instance, arg):
    print(f"rotate_left_64")


def rotate_left_32(instance, arg):
    print(f"rotate_left_32")


def rot_r_64(instance, arg):
    print(f"rot_r_64")


def rot_r_32(instance, arg):
    print(f"rot_r_32")


def and_inverted(instance, arg):
    print(f"and ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    a = seq_b(w_b, 8)
    b = binary_not(seq_b(w_a, 8))
    temp = binary_operation(a, b, "AND")
    instance.initial_regs[reg_d] = inverse_seq_b(temp)


def _xnor(instance, arg):
    print(f"_xor ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    a = seq_b(w_b, 8)
    b = seq_b(w_a, 8)
    temp = binary_not(binary_operation(a, b, "XOR"))
    instance.initial_regs[reg_d] = inverse_seq_b(temp)


def or_inverted(instance, arg):
    print(f"_or")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    a = seq_b(w_b, 8)
    b = binary_not(seq_b(w_a, 8))
    temp = binary_operation(a, b, "OR")
    instance.initial_regs[reg_d] = inverse_seq_b(temp)


def _max(instance, arg):
    print(f"max")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    a = signed_z(w_a, 8)
    b = signed_z(w_b, 8)
    instance.initial_regs[reg_d] = max(a, b)


def max_u(instance, arg):
    print(f"max_u")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    instance.initial_regs[reg_d] = max(w_a, w_b)


def _min(instance, arg):
    print(f"min ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    a = signed_z(w_a, 8)
    b = signed_z(w_b, 8)
    instance.initial_regs[reg_d] = min(a, b)


def min_u(instance, arg):
    print(f"min_u ")
    reg_a, reg_b, reg_d = reg_reg_reg(arg)
    w_a = reg_value(instance, reg_a)
    w_b = reg_value(instance, reg_b)
    instance.initial_regs[reg_d] = min(w_a, w_b)

# Define instruction functions for ind and immediate operations


def store_ind_u8(instance, arg):
    print(f"store_ind_u8 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    w_a = reg_value(instance, reg_a)
    address = w_b + v_x
    content = [w_a % 2**8]
    if valid_address(instance.initial_page_map, address):
        instance.initial_memory = store_value(instance.initial_memory, address, content)


def store_ind_u16(instance, arg):
    print(f"store_ind_u16 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    w_a = reg_value(instance, reg_a)
    serialize = IntegerCodec(2)
    buffer = bytearray(2)
    IntegerCodec.encode_into(serialize, w_a % 2**16, buffer)
    content = list(buffer.rstrip(b'\x00'))
    address = w_b + v_x
    if valid_address(instance.initial_page_map, address):
        instance.initial_memory = store_value(instance.initial_memory, address, content)


def store_ind_u32(instance, arg):
    print(f"store_ind_u32 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    w_a = reg_value(instance, reg_a)
    serialize = IntegerCodec(4)
    buffer = bytearray(4)
    IntegerCodec.encode_into(serialize, w_a % 2 ** 32, buffer)
    content = list(buffer.rstrip(b'\x00'))
    address = w_b + v_x
    if valid_address(instance.initial_page_map, address):
        instance.initial_memory = store_value(instance.initial_memory, address, content)


def store_ind_u64(instance, arg):
    print(f"store_ind_u64 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    w_a = reg_value(instance, reg_a)
    serialize = IntegerCodec(8)
    buffer = bytearray(8)
    IntegerCodec.encode_into(serialize, w_a, buffer)
    content = list(buffer.rstrip(b'\x00'))
    address = w_b + v_x
    if valid_address(instance.initial_page_map, address):
        instance.initial_memory = store_value(instance.initial_memory, address, content)


def load_ind_u8(instance, arg):
    print(f"load_ind_u8 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    instance.initial_args[reg_a] = memory_value(instance.initial_memory, w_b + v_x)


def load_ind_i8(instance, arg):
    print(f"load_ind_i8 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    value = memory_value(instance.initial_memory, w_b + v_x)
    instance.initial_args[reg_a] = inverse_signed_z(signed_z(value, 1), 8)


def load_ind_u16(instance, arg):
    print(f"load_ind_u16 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    value = memory_value(instance.initial_memory, w_b + v_x, w_b + v_x + 2)
    instance.initial_args[reg_a] = IntegerCodec.decode_from(2, value)


def load_ind_i16(instance, arg):
    print(f"load_ind_i16 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = memory_value(instance.initial_memory, w_b + v_x, w_b + v_x + 2)
    value = IntegerCodec.decode_from(2, temp)
    instance.initial_args[reg_a] = inverse_signed_z(signed_z(value, 2), 8)


def load_ind_u32(instance, arg):
    print(f"load_ind_u32 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    value = memory_value(instance.initial_memory, w_b + v_x, w_b + v_x + 4)
    instance.initial_args[reg_a] = IntegerCodec.decode_from(4, value)


def load_ind_i32(instance, arg):
    print(f"load_ind_i32 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = memory_value(instance.initial_memory, w_b + v_x, w_b + v_x + 4)
    value = IntegerCodec.decode_from(4, temp)
    instance.initial_args[reg_a] = inverse_signed_z(signed_z(value, 4), 8)


def load_ind_u64(instance, arg):
    print(f"load_ind_u64 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    value = memory_value(instance.initial_memory, w_b + v_x, w_b + v_x + 8)
    instance.initial_args[reg_a] = IntegerCodec.decode_from(8, value)


def add_imm_32(instance, arg):
    print(f"add_imm_32 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    instance.initial_regs[reg_a] = signed_ext((w_b + v_x) % 2**32, 4)


def add_imm_64(instance, arg):
    print(f"add_imm_64 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    instance.initial_regs[reg_a] = (w_b + v_x) % 2 ** 64


def and_imm(instance, arg):
    print(f"and_imm ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    a = seq_b(w_b, 8)
    b = seq_b(v_x, 8)
    temp = binary_operation(a, b, 'AND')
    instance.initial_regs[reg_a] = inverse_seq_b(temp)


def xor_imm(instance, arg):
    print(f"xor_imm ")


def or_imm(instance, arg):
    print(f"or_imm ")


def mul_imm_32(instance, arg):
    print(f"mul_imm_32 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    instance.initial_regs[reg_a] = signed_ext((w_b*v_x) % 2**32, 4)


def mul_imm_64(instance, arg):
    print(f"mul_imm_64 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    instance.initial_regs[reg_a] = (w_b * v_x) % 2**64


def set_lt_unsigned_imm(instance, arg):
    print(f"set_lt_unsigned_imm ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    instance.initial_regs[reg_a] = w_b < v_x


def set_lt_signed_imm(instance, arg):
    print(f"set_lt_signed_imm ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    instance.initial_regs[reg_a] = signed_z(w_b, 8) < signed_z(v_x, 8)


def shlo_l_imm_32(instance, arg):
    print(f"shlo_l_imm_32 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = w_b * 2**(v_x % 32)
    instance.initial_regs[reg_a] = signed_ext(temp % 2**32, 4)


def shlo_l_imm_64(instance, arg):
    print(f"shlo_l_imm_64 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = w_b * 2**(v_x % 64)
    instance.initial_regs[reg_a] = signed_ext(temp % 2 ** 64, 8)


def  shlo_r_imm_32(instance, arg):
    print(f" shlo_r_imm_32 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = (w_b % 2**32) / (2**(v_x % 32))
    instance.initial_regs[reg_a] = signed_ext(math.floor(temp), 4)


def  shlo_r_imm_64(instance, arg):
    print(f" shlo_r_imm_64 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = w_b / (2 ** (v_x % 32))
    instance.initial_regs[reg_a] = signed_ext(math.floor(temp), 8)


def shar_r_imm_32(instance, arg):
    print(f" shar_r_imm_32 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = (signed_z(w_b % 2**32, 4)) / 2**(v_x % 32)
    instance.initial_regs[reg_a] = inverse_signed_z(math.floor(temp), 8)


def shar_r_imm_64(instance, arg):
    print(f" shar_r_imm_64")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = (signed_z(w_b, 8)) / 2 ** (v_x % 64)
    instance.initial_regs[reg_a] = inverse_signed_z(math.floor(temp), 8)


def neg_add_imm_32(instance, arg):
    print(f"neg_add_imm_32")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = v_x + 2**32 - w_b
    instance.initial_regs[reg_a] = signed_ext(temp % 2**32, 4)


def neg_add_imm_64(instance, arg):
    print(f"neg_add_imm_64 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = v_x + 2 ** 64 - w_b
    instance.initial_regs[reg_a] = temp % 2 ** 64


def set_gt_unsigned_imm(instance, arg):
    print(f"set_gt_unsigned_imm")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    instance.initial_regs[reg_a] = w_b > v_x


def set_gt_signed_imm(instance, arg):
    print(f"set_gt_signed_imm ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    instance.initial_regs[reg_a] = signed_z(w_b, 8) > signed_z(v_x, 8)


def shlo_r_imm_alt_32(instance, arg):
    print(f" shlo_r_imm_alt_32 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = (v_x % 2**32) / 2**(w_b % 32)
    instance.initial_regs[reg_a] = signed_ext(math.floor(temp), 4)


def shlo_r_imm_alt_64(instance, arg):
    print(f" shlo_r_imm_alt_64 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = v_x / 2**(w_b % 64)
    instance.initial_regs[reg_a] = math.floor(temp)


def shar_r_imm_alt_32(instance, arg):
    print(f" shar_r_imm_alt_32 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = signed_z(v_x % 2**32, 4) / 2**(w_b % 32)
    instance.initial_regs[reg_a] = inverse_signed_z(math.floor(temp), 8)


def shar_r_imm_alt_64(instance, arg):
    print(f" shar_r_imm_alt_64 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = signed_z(v_x, 8) / 2 ** (w_b % 64)
    instance.initial_regs[reg_a] = inverse_signed_z(math.floor(temp), 8)


def shlo_l_imm_alt_32(instance, arg):
    print(f"shlo_l_imm_alt_32 ")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = (v_x * 2**(w_b % 32)) % 2**32
    instance.initial_regs[reg_a] = signed_ext(temp, 4)


def shlo_l_imm_alt_64(instance, arg):
    print(f"shlo_l_imm_alt_64")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    temp = (v_x * 2**(w_b % 64)) % 2 ** 64
    instance.initial_regs[reg_a] = temp


def cmov_iz_imm(instance, arg):
    print(f"cmov_iz_imm")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    w_a = reg_value(instance, reg_a)
    if w_b == 0:
        instance.initial_regs[reg_a] = v_x
    else:
        instance.initial_regs[reg_a] = w_a


def cmov_nz_imm(instance, arg):
    print(f"cmov_nz_imm")
    reg_a, reg_b, l_x, v_x = reg_reg_imm(arg)
    w_b = reg_value(instance, reg_b)
    w_a = reg_value(instance, reg_a)
    if w_b != 0:
        instance.initial_regs[reg_a] = v_x
    else:
        instance.initial_regs[reg_a] = w_a


def rot_r_imm_32(instance, arg):
    print(f"rot_r_imm_32")


def rot_r_imm_alt_32(instance, arg):
    print(f"rot_r_imm_alt_32 ")


def rot_r_imm_64(instance, arg):
    print(f"rot_r_imm_64")


def rot_r_imm_alt_64(instance, arg):
    print(f"rot_r_imm_alt_64")


def branch_eq(instance, arg):
    print("branch_eq")


def branch_ne(instance, arg):
    print("branch_ne")


def branch_lt_u(instance, arg):
    print("branch_lt_u")


def branch_lt_s(instance, arg):
    print("branch_lt_s")


def branch_ge_u(instance, arg):
    print("branch_ge_u")


def branch_ge_s(instance, arg):
    print("branch_ge_s")


def store_imm_ind_u8(instance, arg):
    print("store_imm_u8")
    reg_a, l_x, l_y, v_x, v_y = reg_imm_imm(instance, arg)
    w_a = reg_value(instance, reg_a)
    address = w_a + v_x
    content = v_y % 2**8
    if valid_address(instance.initial_page_map, address, True):
        instance.initial_memory = store_value(instance.initial_memory, address, content)


def store_imm_ind_u16(instance, arg):
    print("store_imm_u16")
    reg_a, l_x, l_y, v_x, v_y = reg_imm_imm(instance, arg)
    w_a = reg_value(instance, reg_a)
    address = w_a + v_x
    serialize = IntegerCodec(2)
    buffer = bytearray(2)
    IntegerCodec.encode_into(serialize, v_y % 2 ** 16, buffer)
    content = list(buffer.rstrip(b'\x00'))
    if valid_address(instance.initial_page_map, address, True):
        instance.initial_memory = store_value(instance.initial_memory, address, content)


def store_imm_ind_u32(instance, arg):
    print("store_imm_u32")
    reg_a, l_x, l_y, v_x, v_y = reg_imm_imm(instance, arg)
    w_a = reg_value(instance, reg_a)
    address = w_a + v_x
    serialize = IntegerCodec(4)
    buffer = bytearray(4)
    IntegerCodec.encode_into(serialize, v_y % 2 ** 32, buffer)
    content = list(buffer.rstrip(b'\x00'))
    if valid_address(instance.initial_page_map, address, True):
        instance.initial_memory = store_value(instance.initial_memory, address, content)


def store_imm_ind_u64(instance, arg):
    print("store_imm_u64")
    reg_a, l_x, l_y, v_x, v_y = reg_imm_imm(instance, arg)
    w_a = reg_value(instance, reg_a)
    address = w_a + v_x
    serialize = IntegerCodec(8)
    buffer = bytearray(8)
    IntegerCodec.encode_into(serialize, v_y, buffer)
    content = list(buffer.rstrip(b'\x00'))
    if valid_address(instance.initial_page_map, address, True):
        instance.initial_memory = store_value(instance.initial_memory, address, content)

