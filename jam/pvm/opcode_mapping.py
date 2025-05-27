import copy
import math
from jam.utils.codec.primitives.integers import IntegerCodec
from decimal import Decimal, ROUND_FLOOR
from jam.types.base.integers.fixed import U32, U64, U128
from jam.pvm.memory import Memory, MemoryChunk
from jam.types.base.sequences.bytes.bytes import Bytes, Byte
from jam.pvm.types import Status

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
            70: "store_imm_ind_u8",
            71: "store_imm_ind_u16",
            72: "store_imm_ind_u32",
            73: "store_imm_ind_u64"
        },
        "reg_imm_off": {
            80: "load_imm_jump",
            81: "branch_eq_imm",
            82: "branch_ne_imm",
            83: "branch_lt_u_imm",
            84: "branch_le_u_imm",
            85: "branch_ge_u_imm",
            86: "branch_gt_u_imm",
            87: "branch_lt_s_imm",
            88: "branch_le_s_imm",
            89: "branch_ge_s_imm",
            90: "branch_gt_s_imm",
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
        # GroupInstructionMapper.reg_reg_imm
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
           139: "shlo_r_imm_32",
           152: "shlo_r_imm_64",
           140: "shar_r_imm_32",
           153: "shar_r_imm_64",
           141: "neg_add_imm_32",
           154: "neg_add_imm_64",
           142: "set_gt_unsigned_imm",
           143: "set_gt_signed_imm",
           145: "shlo_r_imm_alt_32",
           156: "shlo_r_imm_alt_64",
           146: "shar_r_imm_alt_32",
           157: "shar_r_imm_alt_64",
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
            180: "load_imm_jump_ind",
        },
        "reg_ext_imm": {
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
            198: "shlo_r_32",
            199: "shar_r_32",
            200: "add_64",
            201: "sub_64",
            202: "mul_64",
            203: "div_u_64",
            204: "div_signed_64",
            205: "rem_u_64",
            206: "rem_signed_64",
            207: "shlo_l_64",
            208: "shlo_r_64",
            209: "shar_r_64",
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
        for group_name, instructions in cls.INSTRUCTION_GROUPS.items():
            if opcode in instructions:
                function_name = instructions[opcode]
                if hasattr(cls, function_name):
                    return group_name, getattr(cls, function_name)
        return opcode, None

    @classmethod
    def execute(cls, opcode: int, *args):
        group, function = cls.get_instruction(opcode)
        if function is None:
            print(f"Opcode {opcode} is unknown.")
            return
        return function(*args)

    @staticmethod
    def signed_ext(num, n):
        return num + (math.floor(num // 2 ** (8 * n - 1))) * (2 ** 64 - 2 ** (8 * n))

    @staticmethod
    def reg_value(instance, r):
        return instance.initial_regs[r]

    @staticmethod
    def increase_counter(instance, count):
        instance.initial_pc += count

    @staticmethod
    def left_rot(bits, shift):
        n = len(bits)  # 64-bit register
        shift = shift % n  # Ensure shift is within bounds
        return bits[-shift:] + bits[:-shift]  # Right shift using slicing

    @staticmethod
    def right_rot(bits, shift):
        n = len(bits)
        return bits[shift % n:] + bits[:shift % n]

    @staticmethod
    def valid_n(buffer, max_n=65):
        max_n = min(max_n, len(buffer))
        _sum = 0
        n = 0  # Store the largest n satisfying the condition
        for i in range(max_n):  # Iterate over possible values of n
            _sum += int(buffer[i])  # Compute cumulative sum
            if _sum == 0:  # Check if sum is zero
                n = i + 1  # Update max valid n
        return n  # Return the maximum valid n

    @staticmethod
    def signed_z(num, n):
        a = int(copy.deepcopy(num))
        if a < (1 << (8 * n - 1)):
            return a
        else:
            return a - (1 << (8 * n))

    @staticmethod
    def branch(instance, b, c):
        if not c:
            instance.initial_pc -= 1
            return {"status": "continue", "value": 0}
        elif b > len(instance.program.instruction_set):
            return {"status": "panic", "value": 0}
        else:
            return {"status": "continue", "value": b}

    @staticmethod
    def d_jump(instance, a):
        j = instance.program.jump_table
        if a == 2 ** 32 - 2 ** 16:
            return {"status": "halt", "value": 0}
        elif a == 0 or a > len(j) * 2 or a % 2 != 0 or j[a // 2 - 1] > len(instance.program.instruction_set):
            return {"status": "panic", "value": 0}
        else:
            return {"status": "continue", "value": j[a // 2 - 1]}

    @staticmethod
    def inverse_signed_z(num, n):
        modulus = 2 ** (8 * n)
        return (modulus + num) % modulus

    @staticmethod
    def seq_b(num, n):
        seq = [(num >> i) & 1 for i in range(8 * n)]
        return ''.join(map(str, [(num >> i) & 1 for i in range(8 * n)]))

    @staticmethod
    def valid_address(page_memory, address, ln=0, writable=None):
        page_number = address // 4096
        offset = int(address % 4096)
        while offset + ln > 4096:
            if U32(page_number) not in page_memory.pages.keys():
                print("one")
                return False
            memory = page_memory.pages[U32(page_number)]
            if memory.access.inaccessible.value:
                print("two")
                return False
            ln -= (4096 - offset)
            offset = 0
            page_number += 1

        if U32(int(page_number)) in page_memory.pages.keys():
            memory = page_memory.pages[U32(page_number)]
            if memory.access.inaccessible.value:
                print("three")
                return False
            return True

        return False

    @staticmethod
    def memory_value(page_memory, address, length=1, is_int=False):
        PAGE_SIZE = 4096
        pages = page_memory.pages  # Dictionary containing memory pages

        # Calculate page index and offset
        page_index = address // PAGE_SIZE
        offset = int(address % PAGE_SIZE)

        result = Bytes([])
        while length > 0:
            if page_index in pages.keys():
                memory_object = pages[page_index]
                values = memory_object.value  # Byte array

                for i in range(offset, min(offset + length, PAGE_SIZE)):
                    if i < len(values):
                        result.append(values[i])
                    else:
                        result.append(Byte(0))  # If index is out of bounds, append 0

                length -= min(length, PAGE_SIZE - offset)
                offset = 0  # Reset offset for next page lookup
            else:
                result.extend(Bytes([Byte(0)] * min(length, PAGE_SIZE - offset)))  # Append zeros for missing page
                length -= min(length, PAGE_SIZE - offset)
                offset = 0  # Reset offset for next page lookup

            page_index += 1  # Move to the next page

        return result

    @staticmethod
    def remove_zeros(data):
        processed_data = []

        for obj in data:
            address = obj.address  # U32 type
            content = obj.contents  # Bytes type
            temp_content = []
            temp_add = int(address)  # Convert U32 to int

            for i, value in enumerate(content):  # Ensure iteration over Bytes
                if int(value) != 0:  # Convert Byte to int before comparison
                    temp_content.append(value)
                else:
                    if temp_content:
                        new_data = Memory(address=U32(temp_add), contents=Bytes(temp_content))
                        processed_data.append(new_data)
                    temp_content = []
                    temp_add = int(address) + i + 1  # Ensure correct address update

            if temp_content:
                new_data = Memory(address=U32(temp_add), contents=Bytes(temp_content))
                processed_data.append(new_data)

        processed_data.sort(key=lambda x: int(x.address))  # Ensure correct sorting
        return processed_data

    @staticmethod
    def merge_indices(data):
        if not data:
            return []

        merged_data = [data[0]]  # Start with the first object

        for i in range(1, len(data)):
            prev = merged_data[-1]
            curr = data[i]

            # Calculate the expected next address based on previous content length
            expected_add = prev.address + len(prev.contents)

            if curr.address == expected_add:
                # Merge current content with previous
                prev.contents.extend(curr.contents)
            else:
                # Add current object as a new entry
                merged_data.append(curr)
        return merged_data

    @staticmethod
    def update_memory(data, address, values):
        for i, val in enumerate(values):
            current_add = address + i
            is_found = False

            for entry in data:
                start_add = entry.address
                content_length = len(entry.contents)

                if start_add <= current_add < start_add + content_length:
                    # print('one')
                    entry.contents[current_add - start_add] = Byte(val)
                    is_found = True
                    break

            if not is_found:
                # print('two', val)
                new_data = Memory(address=current_add, contents=Bytes([val]))
                data.append(new_data)
        data.sort(key=lambda x: x.address)

        return data

    @staticmethod
    def extend_array(arr, num):
        return arr + [0] * (num - len(arr)) if len(arr) < num else arr

    @staticmethod
    def store_value(page_memory, address, values):
        PAGE_SIZE = 4096
        pages = page_memory.pages  # Dictionary containing memory pages
        # Convert integer values to Byte objects
        byte_values = [Byte(int(v)) for v in values]

        page_index = address // PAGE_SIZE
        offset = int(address % PAGE_SIZE)
        length = len(byte_values)
        #print(f"Storing {length} bytes at address {address} (Page: {page_index}, Offset: {offset}, {values})")

        i = 0  # Index for byte_values
        while length > 0:
            if page_index not in pages.keys():
                pages[page_index] = Memory(value=Bytes([Byte(0)] * PAGE_SIZE))  # Ensure full page initialization

            memory_object = pages[page_index]

            # Ensure the value array is large enough (should already be PAGE_SIZE)
            if len(memory_object.value) < PAGE_SIZE:
                memory_object.value.extend([Byte(0)] * (PAGE_SIZE - len(memory_object.value)))

            # Write values into the memory at the correct offset
            for j in range(offset, min(offset + length, PAGE_SIZE)):
                memory_object.value[j] = byte_values[i]
                i += 1

            length -= min(length, PAGE_SIZE - offset)
            offset = 0  # Reset offset for next page lookup
            page_index += 1  # Move to next page

        # print(page_memory)
        return page_memory

    @staticmethod
    def smod(a: int, b: int) -> int:
        if b == 0:
            return a
        return (a // abs(a)) * (abs(a) % abs(b)) if a != 0 else 0

    @staticmethod
    def binary_op(bin_str1, bin_str2, operation):
        # Pad the shorter string with leading zeros
        max_len = max(len(bin_str1), len(bin_str2))
        str1 = bin_str1.zfill(max_len)
        str2 = bin_str2.zfill(max_len)

        if operation == 'AND':
            result = ''.join(str(int(a) & int(b)) for a, b in zip(str1, str2))
        elif operation == 'OR':
            result = ''.join(str(int(a) | int(b)) for a, b in zip(str1, str2))
        elif operation == 'XOR':
            result = ''.join(str(int(a) ^ int(b)) for a, b in zip(str1, str2))
        else:
            raise ValueError("Invalid operation. Choose 'AND', 'OR', or 'XOR'.")

        return result

    @staticmethod
    def binary_not(_str):
        return ''.join('1' if a == '0' else '0' for a in _str)

    @staticmethod
    def inverse_seq_b(_str):
        total_sum = 0  # Initialize sum to 0

        for i, bit in enumerate(_str):
            weighted_value = int(bit) * (2 ** i)  # Convert char to int and apply the same logic
            total_sum += weighted_value  # Add to total sum

        return total_sum  # Return the computed integer

    @staticmethod
    def reg_reg(arg):
        reg_d = min(12, arg[0] % 16)
        reg_a = min(math.floor(arg[0] // 16), 12)
        return int(reg_a), int(reg_d)

    @staticmethod
    def reg_reg_imm(arg):
        ln = len(arg)
        reg_a = min(12, arg[0] % 16)
        reg_b = min(12, arg[0] // 16)
        l_x = min(4, max(0, ln - 1))
        v_x = InstructionMapper.signed_ext(IntegerCodec.decode_from(l_x, arg[1:l_x + 1])[0], l_x)
        return int(reg_a), int(reg_b), l_x, v_x

    @staticmethod
    def reg_imm_imm(arg):
        ln = len(arg)
        reg_a = int(min(12, arg[0] % 16))
        l_x = int(min(4, (math.floor(arg[0]) // 16) % 8))
        l_y = min(4, max(0, ln - l_x - 1))
        v_x = InstructionMapper.signed_ext(IntegerCodec.decode_from(l_x, arg[1:l_x + 1])[0], l_x)
        v_y = InstructionMapper.signed_ext(IntegerCodec.decode_from(l_y, arg[l_x + 1:l_x + l_y + 1])[0], l_y)
        return reg_a, l_x, l_y, v_x, v_y

    @staticmethod
    def reg_imm(arg):
        ln = len(arg)
        reg_a = min(12, arg[0] % 16)
        l_x = min(4, max(0, ln - 1))
        v_x = InstructionMapper.signed_ext(IntegerCodec.decode_from(l_x, arg[1:l_x + 1])[0], l_x)
        return int(reg_a), l_x, v_x

    @staticmethod
    def reg_ext_imm(arg):
        reg_a = min(12, arg[0] % 16)
        v_x = IntegerCodec.decode_from(8, arg[1:9])[0]
        return int(reg_a), v_x

    @staticmethod
    def _imm(arg):
        l_x = min(4, len(arg))
        v_x = InstructionMapper.signed_ext(IntegerCodec.decode_from(l_x, arg[0:l_x])[0], l_x)
        return v_x

    @staticmethod
    def imm_imm(arg):
        ln = len(arg)
        l_x = int(min(4, arg[0] % 8))
        l_y = min(4, max(0, (ln - l_x - 1)))
        v_x = InstructionMapper.signed_ext(IntegerCodec.decode_from(l_x, arg[1:l_x + 1])[0], l_x)
        v_y = InstructionMapper.signed_ext(IntegerCodec.decode_from(l_y, arg[l_x + 1:l_x + l_y + 1])[0], l_y)
        return l_x, l_y, v_x, v_y

    @staticmethod
    def count_set_bits(_str: str) -> int:
        if not all(c in '01' for c in _str):
            raise ValueError("Not a valid binary string.")

        return _str.count('1')

    @staticmethod
    def reg_reg_reg(arg):
        reg_a = min(12, arg[0] % 16)
        reg_b = min(12, arg[0] // 16)
        reg_d = min(12, arg[1])
        return int(reg_a), int(reg_b), int(reg_d)

    @staticmethod
    def offset(arg):
        ln = len(arg)
        l_x = min(4, ln)
        v_x = InstructionMapper.signed_z(IntegerCodec.decode_from(l_x, arg[0:l_x + 1])[0], l_x)
        return v_x

    @staticmethod
    def reg_imm_off(arg):
        ln = len(arg)
        reg_a = int(min(12, arg[0] % 16))
        l_x = int(min(4, math.floor((arg[0] // 16)) % 8))
        l_y = min(4, max(0, ln - l_x - 1))
        v_x = InstructionMapper.signed_ext(IntegerCodec.decode_from(l_x, arg[1:l_x + 1])[0], l_x)
        v_y = InstructionMapper.signed_z(IntegerCodec.decode_from(l_y, arg[l_x + 1:l_x + l_y + 1])[0], l_y)
        return reg_a, v_x, v_y

    @staticmethod
    def reg_reg_off(arg):
        ln = len(arg)
        reg_a = int(min(12, arg[0] % 16))
        reg_b = int(min(12, math.floor(arg[0] // 16)))
        l_x = min(4, max(0, ln - 1))
        v_x = InstructionMapper.signed_z(IntegerCodec.decode_from(l_x, arg[1:l_x + 1])[0], l_x)
        return reg_a, reg_b, v_x

    @staticmethod
    def reg_reg_imm_imm(arg):
        ln = len(arg)
        reg_a = int(min(12, arg[0] % 16))
        reg_b = int(min(12, math.floor(arg[0] // 16)))
        l_x = int(min(4, arg[1] % 8))
        l_y = min(4, max(0, ln - l_x - 2))
        v_x = InstructionMapper.signed_ext(IntegerCodec.decode_from(l_x, arg[2:2 + l_x])[0], l_x)
        v_y = InstructionMapper.signed_ext(IntegerCodec.decode_from(l_y, arg[2 + l_x:2 + l_x + l_y])[0], l_y)
        return reg_a, reg_b, v_x, v_y

    @staticmethod
    def add_32(instance, arg):
        print("add_32")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        n = (U64(instance.initial_regs[reg_a] & 0xFFFFFFFF) + U64(instance.initial_regs[reg_b] & 0xFFFFFFFF)) & 0xFFFFFFFF
        _sum = InstructionMapper.signed_ext(n, 4)
        instance.initial_regs[reg_d] = _sum

    @staticmethod
    def trap(instance, arg):
        print("trap")
        InstructionMapper.increase_counter(instance, 0)
        return "panic"

    @staticmethod
    def fallthrough(instance, arg):
        print("fallthrough")
        InstructionMapper.increase_counter(instance, 1)
        return "fallthrough"

    @staticmethod
    def jump_ind(instance, arg):
        print(f"jump_ind ")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        result = InstructionMapper.d_jump(instance, (w_a + v_x) % 2 ** 32)
        if result["status"] == "continue":
            instance.initial_pc = U64(result["value"])
            return result["value"]
        elif result["status"] == "panic":
            return "panic"
        else:
            return "halt"

    @staticmethod
    def load_imm(instance, arg):
        print(f"load_imm")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        instance.initial_regs[reg_a] = U64(v_x)
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def load_u8(instance, arg):
        print(f"load_u8 ")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, v_x)
        if is_valid:
            u_vx = InstructionMapper.memory_value(instance.initial_memory, v_x)[0]
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            temp = InstructionMapper.bit_to_int(u_vx.value)
            instance.initial_regs[reg_a] = U64(temp)
        else:
            return "page-fault"

    @staticmethod
    def bit_to_int(bit_list):
        return int("".join(str(int(b)) for b in bit_list), 2)  # Convert bit list to binary string, then to int

    @staticmethod
    def load_i8(instance, arg):
        print(f"load_i8 ")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, v_x)
        if is_valid:
            u_vx = InstructionMapper.memory_value(instance.initial_memory, v_x, 1, True)[0]
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            temp = InstructionMapper.bit_to_int(u_vx.value)
            instance.initial_regs[reg_a] = U64(InstructionMapper.signed_ext(temp, 1))
        else:
            return "page-fault"

    @staticmethod
    def load_u16(instance, arg):
        print(f"load_u16 ")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, v_x, 2)
        if is_valid:
            u_vx = InstructionMapper.memory_value(instance.initial_memory, v_x, 2)
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            temp = []
            for v in u_vx:
                temp.append(int(v))
            instance.initial_regs[reg_a] = U64(IntegerCodec.decode_from(2, bytes(temp))[0])
        else:
            return "page-fault"

    @staticmethod  
    def load_i16(instance, arg):
        print(f"load_i16 ")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, v_x, 2)
        if is_valid:
            u_vx = InstructionMapper.memory_value(instance.initial_memory, v_x, 2, True)
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            instance.initial_regs[reg_a] = U64(InstructionMapper.signed_ext(IntegerCodec.decode_from(2, bytes(u_vx))[0], 2))
        else:
            return "page-fault"

    @staticmethod
    def load_u32(instance, arg):
        print(f"load_u32 ")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, v_x, 4)
        if is_valid:
            u_vx = InstructionMapper.memory_value(instance.initial_memory, v_x, 4)
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            temp = []
            for v in u_vx:
                temp.append(int(v))
            instance.initial_regs[reg_a] = U64(IntegerCodec.decode_from(4, bytes(temp))[0])
        else:
            return "page-fault"

    @staticmethod
    def load_i32(instance, arg):
        print(f"load_i32 ")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, v_x, 4)
        if is_valid:
            u_vx = InstructionMapper.memory_value(instance.initial_memory, v_x, 4,True)
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            instance.initial_regs[reg_a] = U64(InstructionMapper.signed_ext(IntegerCodec.decode_from(4, bytes(u_vx))[0], 4))
        else:
            return "page-fault"

    # Define all instruction functions
    @staticmethod
    def load_u64(instance, arg):
        print(f"load_u64")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, v_x, 8)
        if is_valid:
            u_vx = InstructionMapper.memory_value(instance.initial_memory, v_x, 8)
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            instance.initial_regs[reg_a] = U64(IntegerCodec.decode_from(8, bytes(u_vx))[0])
        else:
            return "page-fault"

    @staticmethod
    def store_u8(instance, arg):
        print(f"store_u8 ")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        address = v_x
        print(address)
        contents = [w_a % 2 ** 8]
        if InstructionMapper.valid_address(instance.initial_memory, address):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, address, contents)
        else:
            return "page-fault"

    @staticmethod
    def store_u16(instance, arg):
        print(f"store_u16 ")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        address = v_x
        serialize = IntegerCodec(2)
        buffer = bytearray(2)
        IntegerCodec.encode_into(serialize, w_a % 2 ** 16, buffer)
        contents = list(buffer.rstrip(b'\x00'))
        if InstructionMapper.valid_address(instance.initial_memory, address, 2):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            contents = InstructionMapper.extend_array(contents, 2)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, address, contents)
        else:
            return "page-fault"

    @staticmethod
    def store_u32(instance, arg):
        print(f"store_u32 ")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        address = v_x
        serialize = IntegerCodec(4)
        buffer = bytearray(4)
        IntegerCodec.encode_into(serialize, w_a % 2 ** 32, buffer)
        contents = list(buffer.rstrip(b'\x00'))
        if InstructionMapper.valid_address(instance.initial_memory, address):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            contents = InstructionMapper.extend_array(contents, 4)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, address, contents)
        else:
            return "page-fault"

    @staticmethod
    def store_u64(instance, arg):
        print(f"store_u64 ")
        reg_a, l_a, v_x = InstructionMapper.reg_imm(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        address = v_x
        serialize = IntegerCodec(8)
        buffer = bytearray(8)
        IntegerCodec.encode_into(serialize, w_a, buffer)
        contents = list(buffer.rstrip(b'\x00'))
        if InstructionMapper.valid_address(instance.initial_memory, address, 8):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            contents = InstructionMapper.extend_array(contents, 8)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, address, contents)
        else:
            return "page-fault"

    @staticmethod
    def load_imm_jump(instance, arg):
        print(f"load_imm_jump ")
        reg_a, v_x, v_y = InstructionMapper.reg_imm_off(arg)
        instance.initial_regs[reg_a] = U64(v_x)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_y, True)
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_eq_imm(instance, arg):
        print(f"branch_eq_imm ")
        reg_a, v_x, v_y = InstructionMapper.reg_imm_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_y, w_a == v_x)
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_ne_imm(instance, arg):
        print(f"branch_ne_imm ")
        reg_a, v_x, v_y = InstructionMapper.reg_imm_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_y, w_a != v_x)
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_lt_u_imm(instance, arg):
        print(f"branch_le_u_imm ")
        reg_a, v_x, v_y = InstructionMapper.reg_imm_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_y, w_a < v_x)
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_le_u_imm(instance, arg):
        print(f"branch_le_or_equal_u_imm ")
        reg_a, v_x, v_y = InstructionMapper.reg_imm_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_y, w_a <= v_x)
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_ge_u_imm(instance, arg):
        print(f"branch_gt_or_equal_u_imm ")
        reg_a, v_x, v_y = InstructionMapper.reg_imm_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_y, w_a >= v_x)
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_gt_u_imm(instance, arg):
        print(f"branch_gt_u_imm ")
        reg_a, v_x, v_y = InstructionMapper.reg_imm_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_y, w_a > v_x)
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_lt_s_imm(instance, arg):
        print(f"branch_le_s_imm ")
        reg_a, v_x, v_y = InstructionMapper.reg_imm_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_y, InstructionMapper.signed_z(w_a, 8) < InstructionMapper.signed_z(v_x, 8))
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_le_s_imm(instance, arg):
        print(f"branch_le_or_equal_signed_imm ")
        reg_a, v_x, v_y = InstructionMapper.reg_imm_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_y, InstructionMapper.signed_z(w_a, 8) <= InstructionMapper.signed_z(v_x, 8))
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_ge_s_imm(instance, arg):
        print(f"branch_gt_or_equal_signed_imm ")
        reg_a, v_x, v_y = InstructionMapper.reg_imm_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_y, InstructionMapper.signed_z(w_a, 8) >= InstructionMapper.signed_z(v_x, 8))
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_gt_s_imm(instance, arg):
        print(f"branch_gt_signed_imm ")
        reg_a, v_x, v_y = InstructionMapper.reg_imm_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_y, InstructionMapper.signed_z(w_a, 8) > InstructionMapper.signed_z(v_x, 8))
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def jump(instance, arg):
        print(f"jump ")
        v_x = InstructionMapper.offset(arg)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_x, True)
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def ecalli(instance, arg):
        print(f"ecalli ")
        host_status = Status.HOST.with_number(InstructionMapper._imm(arg))
        return host_status

    @staticmethod
    def store_imm_u8(instance, arg):
        print(f"store_imm_u8 ")
        l_x, l_y, v_x, v_y = InstructionMapper.imm_imm(arg)
        if InstructionMapper.valid_address(instance.initial_memory, v_x, writable=True):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, v_x, [v_y % 2 ** 8])
        else:
            return "page-fault"

    @staticmethod
    def store_imm_u16(instance, arg):
        print(f"store_imm_u16")
        l_x, l_y, v_x, v_y = InstructionMapper.imm_imm(arg)
        serialize = IntegerCodec(2)
        buffer = bytearray(2)
        IntegerCodec.encode_into(serialize, v_y % 2 ** 16, buffer)
        contents = list(buffer.rstrip(b'\x00'))
        address = InstructionMapper.valid_address(instance.initial_memory, v_x, 2, writable=True)
        if address:
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            contents = InstructionMapper.extend_array(contents, 2)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, v_x, contents)
        else:
            return "page-fault"

    @staticmethod
    def store_imm_u32(instance, arg):
        print(f"store_imm_u32")
        l_x, l_y, v_x, v_y = InstructionMapper.imm_imm(arg)
        serialize = IntegerCodec(4)
        buffer = bytearray(4)
        IntegerCodec.encode_into(serialize, v_y % 2 ** 32, buffer)
        contents = list(buffer.rstrip(b'\x00'))
        address = InstructionMapper.valid_address(instance.initial_memory, v_x, 4, writable=True)
        if address:
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            contents = InstructionMapper.extend_array(contents, 4)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, v_x, contents)
        else:
            return "page-fault"

    @staticmethod
    def store_imm_u64(instance, arg):
        print(f"store_imm_u64 ")
        l_x, l_y, v_x, v_y = InstructionMapper.imm_imm(arg)
        serialize = IntegerCodec(8)
        buffer = bytearray(8)
        IntegerCodec.encode_into(serialize, v_y, buffer)
        contents = list(buffer.rstrip(b'\x00'))
        address = InstructionMapper.valid_address(instance.initial_memory, v_x, 8, writable=True)
        if address:
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            contents = InstructionMapper.extend_array(contents, 8)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, v_x, contents)
        else:
            return "page-fault"

    @staticmethod
    def move_reg(instance, arg):
        print(f"move_reg ")
        reg_a, reg_d = InstructionMapper.reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        instance.initial_regs[reg_d] = w_a
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def sbrk(instance, arg):
        print("sbrk")

    @staticmethod
    def count_set_bits_64(instance, arg):
        print("count_set_bits_64")
        reg_a, reg_d = InstructionMapper.reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        instance.initial_regs[reg_d] = U64(InstructionMapper.count_set_bits(InstructionMapper.seq_b(w_a, 8)))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def count_set_bits_32(instance, arg):
        print("count_set_bits_32")
        reg_a, reg_d = InstructionMapper.reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        instance.initial_regs[reg_d] = U64(InstructionMapper.count_set_bits(InstructionMapper.seq_b(w_a % 2 ** 32, 4)))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def count_leading_zero_bits_32(instance, arg):
        print("count_leading_zero_bits_32")
        reg_a, reg_d = InstructionMapper.reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        temp = InstructionMapper.seq_b(w_a % 2 ** 32, 4)
        temp = temp[::-1]
        instance.initial_regs[reg_d] = U64(InstructionMapper.valid_n(temp, 33))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def count_leading_zero_bits_64(instance, arg):
        print("count_leading_zero_bits_64")
        reg_a, reg_d = InstructionMapper.reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        temp = InstructionMapper.seq_b(w_a, 8)
        temp = temp[::-1]
        instance.initial_regs[reg_d] = U64(InstructionMapper.valid_n(temp, 65))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def count_trailing_zero_bits_64(instance, arg):
        print("count_trailing_zero_bits_64")
        reg_a, reg_d = InstructionMapper.reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        temp = InstructionMapper.seq_b(w_a, 8)
        instance.initial_regs[reg_d] = U64(InstructionMapper.valid_n(temp, 65))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def count_trailing_zero_bits_32(instance, arg):
        print("count_trailing_zero_bits_32")
        reg_a, reg_d = InstructionMapper.reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        temp = InstructionMapper.seq_b(w_a % 2 ** 32, 4)
        instance.initial_regs[reg_d] = U64(InstructionMapper.valid_n(temp, 33))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def sign_extend_8(instance, arg):
        print("sign_extend_8")
        reg_a, reg_d = InstructionMapper.reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_signed_z(InstructionMapper.signed_z(w_a % 2 ** 8, 1), 8))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def sign_extend_16(instance, arg):
        print("sign_extend_16")
        reg_a, reg_d = InstructionMapper.reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_signed_z(InstructionMapper.signed_z(w_a % 2 ** 16, 2), 8))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def zero_extend_16(instance, arg):
        print("zero_extend_16")
        reg_a, reg_d = InstructionMapper.reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        instance.initial_regs[reg_d] = U64(w_a % 2 ** 16)
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def reverse_byte(instance, arg):
        print("reverse_byte")
        reg_a, reg_d = InstructionMapper.reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        serialize = IntegerCodec(8)
        buffer = bytearray(8)
        IntegerCodec.encode_into(serialize, w_a, buffer)
        temp = buffer[::-1]
        instance.initial_regs[reg_d] = U64(IntegerCodec.decode_from(8, temp)[0])
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def load_imm_jump_ind(instance, arg):
        print(f"load_imm_jump_ind ")
        reg_a, reg_b, v_x, v_y = InstructionMapper.reg_reg_imm_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        instance.initial_regs[reg_a] = U64(v_x)
        result = InstructionMapper.d_jump(instance, (w_b + v_y) % 2 ** 32)
        if result["status"] == "continue":
            instance.initial_pc = U64(result["value"])
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def load_imm_64(instance, arg):
        print(f"load_imm_64 ")
        reg_a, v_x = InstructionMapper.reg_ext_imm(arg)
        instance.initial_regs[reg_a] = U64(v_x)
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def sub_32(instance, arg):
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        instance.initial_regs[reg_d] = U64(InstructionMapper.signed_ext(((w_a + 2 ** 32 - (w_b % 2 ** 32)) % 2 ** 32), 4))
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        print(f"sub_32 ")

    @staticmethod
    def mul_32(instance, arg):
        print(f"mul_32 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.signed_ext((w_a * w_b) % 2 ** 32, 4))

    @staticmethod
    def div_u_32(instance, arg):
        print(f"div_u_32 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        if instance.initial_regs[reg_b] % 2 ** 32 == 0:
            instance.initial_regs[reg_d] = U64(2 ** 64 - 1)
        else:
            instance.initial_regs[reg_d] = U64(InstructionMapper.signed_ext(
                math.floor((instance.initial_regs[reg_a] % 2 ** 32) // (instance.initial_regs[reg_b] % 2 ** 32)), 4))

    @staticmethod
    def div_signed_32(instance, arg):
        print(f"div_signed_32 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        a = InstructionMapper.signed_z(w_a % 2 ** 32, 4)
        b = InstructionMapper.signed_z(w_b % 2 ** 32, 4)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        if b == 0:
            instance.initial_regs[reg_d] = U64(2 ** 64 - 1)
        elif a == -2 ** 31 and b == -1:
            instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_signed_z(a, 8))
        else:
            instance.initial_regs[reg_d] = U64(int(InstructionMapper.inverse_signed_z(Decimal(a) // Decimal(b), 8)))

    @staticmethod
    def rem_u_32(instance, arg):
        print(f"rem_u_32 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        if w_b % 2 ** 32 == 0:
            instance.initial_regs[reg_d] = InstructionMapper.signed_ext(w_a % 2 ** 32, 4)
        else:
            instance.initial_regs[reg_d] = InstructionMapper.signed_ext((w_a % 2 ** 32) % (w_b % 2 ** 32), 4)

    @staticmethod
    def rem_signed_32(instance, arg):
        print(f"rem_signed_32 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        a = InstructionMapper.signed_z(w_a % 2 ** 32, 4)
        b = InstructionMapper.signed_z(w_b % 2 ** 32, 4)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        if b == 0:
            instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_signed_z(a, 8))
        elif a == -2 ** 31 and b == -1:
            instance.initial_regs[reg_d] = U64(0)
        else:
            instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_signed_z(InstructionMapper.smod(a, b), 8))

    @staticmethod
    def shlo_l_32(instance, arg):
        print(f"shlo_l_32 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.signed_ext((w_a * 2 ** (w_b % 32)) % 2 ** 32, 4))

    @staticmethod
    def shlo_r_32(instance, arg):
        print(f" shlo_r_32 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.signed_ext(
            math.floor((w_a % 2 ** 32) // 2 ** (w_b % 32)), 4))

    @staticmethod
    def shar_r_32(instance, arg):
        print(f" shar_r_32 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        _b = int(instance.initial_regs[reg_b])
        a = int(InstructionMapper.signed_z(instance.initial_regs[reg_a] % 2 ** 32, 4))
        b = a // 2 ** (_b % 32)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_signed_z(math.floor(b), 8))

    @staticmethod
    def add_64(instance, arg):
        print(f"add_64 ")
        reg1 = min(arg[0] % 16, 12)
        reg2 = min(math.floor(arg[0] // 16), 12)
        reg3 = min(12, arg[1])
        w_a = int(InstructionMapper.reg_value(instance, reg1))
        w_b = int(InstructionMapper.reg_value(instance, reg2))
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        _sum = (w_a + w_b) % 2**64
        instance.initial_regs[int(reg3)] = U64(_sum)

    @staticmethod
    def sub_64(instance, arg):
        print(f"sub_64 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        a: int = int(copy.deepcopy(instance.initial_regs[reg_a]))
        b: int = int(copy.deepcopy(instance.initial_regs[reg_b]))
        print(a, b)
        res: int = abs(((a - b) % 2**64))
        # if res < 0:
        #     res = 0 - res
        instance.initial_regs[reg_d] = U64(res)

    @staticmethod
    def mul_64(instance, arg):
        print(f"mul_64 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64((w_a * w_b) % 2 ** 64)

    @staticmethod
    def div_u_64(instance, arg):
        print(f"div_u_64 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        if instance.initial_regs[reg_b] == 0:
            instance.initial_regs[reg_d] = U64(2 ** 64 - 1)
        else:
            instance.initial_regs[reg_d] = instance.initial_regs[reg_a] // instance.initial_regs[reg_b]

    @staticmethod
    def div_signed_64(instance, arg):
        print(f"div_signed_64 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        a = InstructionMapper.signed_z(w_a, 8)
        b = InstructionMapper.signed_z(w_b, 8)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        if w_b == 0:
            instance.initial_regs[reg_d] = U64((1 << 64) - 1)
        elif a == -(1 << 63) and b == -1:
            instance.initial_regs[reg_d] = w_a
        else:
            instance.initial_regs[reg_d] = U64(int(InstructionMapper.inverse_signed_z(Decimal(a) // Decimal(b), 8)))

    @staticmethod
    def rem_u_64(instance, arg):
        print(f"rem_u_64 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        if instance.initial_regs[reg_b] == 0:
            instance.initial_regs[reg_d] = instance.initial_regs[reg_a]
        else:
            instance.initial_regs[reg_d] = instance.initial_regs[reg_a] % instance.initial_regs[reg_b]

    @staticmethod
    def rem_signed_64(instance, arg):
        print(f"rem_signed_64 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        a = InstructionMapper.signed_z(w_a, 8)
        b = InstructionMapper.signed_z(w_b, 8)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        if w_b == 0:
            instance.initial_regs[reg_d] = U64(instance.initial_regs[reg_a])
        elif a == -2 ** 63 and b == -1:
            instance.initial_regs[reg_d] = U64(0)
        else:
            instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_signed_z(InstructionMapper.smod(a, b), 8))

    @staticmethod
    def shlo_l_64(instance, arg):
        print(f"shlo_l_64 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        a = 2 ** (w_b % 64)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64((w_a * a) % 2 ** 64)

    @staticmethod
    def shlo_r_64(instance, arg):
        print(f" shlo_r_64 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(w_a // (1 << (w_b % 64)))

    @staticmethod
    def shar_r_64(instance, arg):
        print(f" shar_r_64 ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        a = InstructionMapper.signed_z(w_a, 8)
        b = 1 << (w_b % 64)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_signed_z(a // b, 8))

    @staticmethod
    def _and(instance, arg):
        print(f"and ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        a = InstructionMapper.seq_b(w_b.value, 8)
        b = InstructionMapper.seq_b(w_a.value, 8)
        temp = InstructionMapper.binary_op(a, b, "AND")
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_seq_b(temp))

    @staticmethod
    def _xor(instance, arg):
        print(f"_xor ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        a = InstructionMapper.seq_b(w_b.value, 8)
        b = InstructionMapper.seq_b(w_a.value, 8)
        temp = InstructionMapper.binary_op(a, b, "XOR")
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_seq_b(temp))

    @staticmethod
    def _or(instance, arg):
        print(f"_or")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        a = InstructionMapper.seq_b(w_b.value, 8)
        b = InstructionMapper.seq_b(w_a.value, 8)
        temp = InstructionMapper.binary_op(a, b, "OR")
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_seq_b(temp))

    @staticmethod
    def mul_upper_signed_signed(instance, arg):
        print(f"mul_upper_signed_signed ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        a = InstructionMapper.signed_z(w_a, 8)
        b = InstructionMapper.signed_z(w_b, 8)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_signed_z(math.floor((a * b) // 2 ** 64), 8))

    @staticmethod
    def mul_upper_u_u(instance, arg):
        print(f"mul_upper_u_u ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(math.floor((w_a * w_b) // 2 ** 64))

    @staticmethod
    def mul_upper_signed_u(instance, arg):
        print(f"mul_upper_signed_u")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        a = InstructionMapper.signed_z(w_a, 8)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_signed_z(math.floor((a * w_b) // 2 ** 64), 8))

    @staticmethod
    def set_le_than_u(instance, arg):
        print(f"set_le_than_u ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(w_a < w_b)

    @staticmethod
    def set_le_than_signed(instance, arg):
        print(f"set_le_than_signed")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        a = InstructionMapper.signed_z(w_a, 8)
        b = InstructionMapper.signed_z(w_b, 8)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(a < b)

    @staticmethod
    def cmov_iz(instance, arg):
        print(f"cmov_iz")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        if w_b == 0:
            instance.initial_regs[reg_d] = w_a
        else:
            instance.initial_regs[reg_d] = instance.initial_regs[reg_d]

    @staticmethod
    def cmov_nz(instance, arg):
        print(f"cmov_nz")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        if w_b != 0:
            instance.initial_regs[reg_d] = w_a
        else:
            instance.initial_regs[reg_d] = instance.initial_regs[reg_d]

    @staticmethod
    def rotate_left_64(instance, arg):
        print(f"rotate_left_64")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = InstructionMapper.left_rot(InstructionMapper.seq_b(w_a, 8), w_b)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_seq_b(temp))

    @staticmethod
    def rotate_left_32(instance, arg):
        print(f"rotate_left_32")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = InstructionMapper.left_rot(InstructionMapper.seq_b(w_a, 4), w_b)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.signed_ext(InstructionMapper.inverse_seq_b(temp), 4))

    @staticmethod
    def rot_r_64(instance, arg):
        print(f"rot_r_64")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = InstructionMapper.right_rot(InstructionMapper.seq_b(w_a, 8), w_b)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_seq_b(temp))

    @staticmethod
    def rot_r_32(instance, arg):
        print(f"rot_r_32")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = InstructionMapper.right_rot(InstructionMapper.seq_b(w_a, 4), w_b)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.signed_ext(InstructionMapper.inverse_seq_b(temp), 4))

    @staticmethod
    def and_inverted(instance, arg):
        print(f"and_inverted")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        a = InstructionMapper.seq_b(w_a, 8)
        b = InstructionMapper.binary_not(InstructionMapper.seq_b(w_b, 8))
        temp = InstructionMapper.binary_op(a, b, "AND")
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_seq_b(temp))

    @ staticmethod
    def _xnor(instance, arg):
        print(f"_xor ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        a = InstructionMapper.seq_b(w_b, 8)
        b = InstructionMapper.seq_b(w_a, 8)
        temp = InstructionMapper.binary_not(InstructionMapper.binary_op(a, b, "XOR"))
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_seq_b(temp))

    @staticmethod
    def or_inverted(instance, arg):
        print(f"_or_inverted")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        a = InstructionMapper.seq_b(w_a, 8)
        b = InstructionMapper.binary_not(InstructionMapper.seq_b(w_b, 8))
        temp = InstructionMapper.binary_op(a, b, "OR")
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_seq_b(temp))

    @staticmethod
    def _max(instance, arg):
        print(f"max")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        a = InstructionMapper.signed_z(w_a, 8)
        b = InstructionMapper.signed_z(w_b, 8)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_signed_z(max(a, b), 8))

    @staticmethod
    def max_u(instance, arg):
        print(f"max_u")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(max(w_a, w_b))

    @staticmethod
    def _min(instance, arg):
        print(f"min ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        a = InstructionMapper.signed_z(w_a, 8)
        b = InstructionMapper.signed_z(w_b, 8)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(InstructionMapper.inverse_signed_z(min(a, b), 8))

    @staticmethod
    def min_u(instance, arg):
        print(f"min_u ")
        reg_a, reg_b, reg_d = InstructionMapper.reg_reg_reg(arg)
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_d] = U64(min(w_a, w_b))

    @staticmethod
    def store_ind_u8(instance, arg):
        print(f"store_ind_u8 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        address = (w_b + v_x) % 2 ** 64
        content = [w_a % 2 ** 8]
        if InstructionMapper.valid_address(instance.initial_memory, address):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, address, content)
        else:
            return "page-fault"

    @staticmethod
    def store_ind_u16(instance, arg):
        print(f"store_ind_u16 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        serialize = IntegerCodec(2)
        buffer = bytearray(2)
        IntegerCodec.encode_into(serialize, w_a % 2 ** 16, buffer)
        content = list(buffer.rstrip(b'\x00'))
        address = (w_b + v_x) % 2 ** 64
        if InstructionMapper.valid_address(instance.initial_memory, address, 2):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            content = InstructionMapper.extend_array(content, 2)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, address, content)
        else:
            return "page-fault"

    @staticmethod
    def store_ind_u32(instance, arg):
        print(f"store_ind_u32 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        serialize = IntegerCodec(4)
        buffer = bytearray(4)
        IntegerCodec.encode_into(serialize, w_a % 2 ** 32, buffer)
        content = list(buffer.rstrip(b'\x00'))
        address = (w_b + v_x) % 2 ** 64
        if InstructionMapper.valid_address(instance.initial_memory, address, 4):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            content = InstructionMapper.extend_array(content, 4)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, address, content)
        else:
            return "page-fault"

    @staticmethod
    def store_ind_u64(instance, arg):
        print(f"store_ind_u64 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        address = (w_b + v_x) % 2 ** 64
        if InstructionMapper.valid_address(instance.initial_memory, address, 8):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            serialize = IntegerCodec(8)
            buffer = bytearray(8)
            IntegerCodec.encode_into(serialize, w_a, buffer)
            content = list(buffer.rstrip(b'\x00'))
            content = InstructionMapper.extend_array(content, 8)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, address, content)
        else:
            print(f"memory inaccessible:{address}")
            return "page-fault"

    @staticmethod
    def load_ind_u8(instance, arg):
        print(f"load_ind_u8 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        address = int((w_b + v_x) % 2 ** 64)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, address)
        if is_valid:
            temp = InstructionMapper.memory_value(instance.initial_memory, address)[0]
            temp = InstructionMapper.bit_to_int(temp.value)
            instance.initial_regs[reg_a] = U64(int(temp))
            InstructionMapper.increase_counter(instance, len(arg) + 1)
        else:
            return "page-fault"

    @staticmethod
    def load_ind_i8(instance, arg):
        print(f"load_ind_i8 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        address = int((w_b + v_x) % 2 ** 64)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, address)
        if is_valid:
            value = InstructionMapper.memory_value(instance.initial_memory, address)[0]
            temp = InstructionMapper.bit_to_int(value.value)
            instance.initial_regs[reg_a] = U64(InstructionMapper.inverse_signed_z(InstructionMapper.signed_z(temp, 1), 8))
            InstructionMapper.increase_counter(instance, len(arg) + 1)
        else:
            return "page-fault"

    @staticmethod
    def load_ind_u16(instance, arg):
        print(f"load_ind_u16 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        address = int((w_b + v_x) % 2 ** 64)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, address, 2)
        if is_valid:
            value = InstructionMapper.memory_value(instance.initial_memory, address, 2)
            temp = []
            for v in value:
                temp.append(int(v))
            instance.initial_regs[reg_a] = U64(IntegerCodec.decode_from(2, bytes(temp))[0])
            InstructionMapper.increase_counter(instance, len(arg) + 1)
        else:
            return "page-fault"

    @staticmethod
    def load_ind_i16(instance, arg):
        print(f"load_ind_i16 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        address = int((w_b + v_x) % 2**64)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, address, 2)
        if is_valid:
            temp = InstructionMapper.memory_value(instance.initial_memory, address, 2)
            temp2 = []
            for t in temp:
                temp2.append(int(t))
            value = IntegerCodec.decode_from(2, bytes(temp2))[0]
            instance.initial_regs[reg_a] = U64(InstructionMapper.inverse_signed_z(InstructionMapper.signed_z(value, 2), 8))
            InstructionMapper.increase_counter(instance, len(arg) + 1)
        else:
            return "page-fault"

    @staticmethod
    def load_ind_u32(instance, arg):
        print(f"load_ind_u32 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        address = int((w_b + v_x) % 2 ** 64)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, address, 4)
        if is_valid:
            value = InstructionMapper.memory_value(instance.initial_memory, address, 4)
            temp = []
            for v in value:
                temp.append(int(v))
            instance.initial_regs[reg_a] = U64(IntegerCodec.decode_from(4, bytes(temp))[0])
            InstructionMapper.increase_counter(instance, len(arg) + 1)
        else:
            return "page-fault"

    @staticmethod
    def load_ind_i32(instance, arg):
        print(f"load_ind_i32 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        address = int((w_b + v_x) % 2 ** 64)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, address, 4)
        if is_valid:
            temp = InstructionMapper.memory_value(instance.initial_memory, address, 4)
            temp2 = []
            for t in temp:
                temp2.append(int(t))
            value = IntegerCodec.decode_from(4, bytes(temp2))[0]
            instance.initial_regs[reg_a] = U64(InstructionMapper.inverse_signed_z(InstructionMapper.signed_z(value, 4), 8))
            InstructionMapper.increase_counter(instance, len(arg) + 1)
        else:
            return "page-fault"

    @staticmethod
    def load_ind_u64(instance, arg):
        print(f"load_ind_u64 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        address = int((w_b + v_x) % 2 ** 64)
        is_valid = InstructionMapper.valid_address(instance.initial_memory, address, 8)
        if is_valid:
            value = InstructionMapper.memory_value(instance.initial_memory, address, 8)
            temp = []
            for v in value:
                temp.append(int(v))
            instance.initial_regs[reg_a] = U64(IntegerCodec.decode_from(8, bytes(temp))[0])
            InstructionMapper.increase_counter(instance, len(arg) + 1)
        else:
            return "page-fault"

    @staticmethod
    def add_imm_32(instance, arg):
        print(f"add_imm_32 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        instance.initial_regs[reg_a] = U64(InstructionMapper.signed_ext((w_b + v_x) % 2 ** 32, 4))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def add_imm_64(instance, arg):
        print(f"add_imm_64 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        instance.initial_regs[reg_a] = U64((w_b % 2 ** 64 + v_x % 2 ** 64) % 2 ** 64)
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def and_imm(instance, arg):
        print(f"and_imm ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        a = InstructionMapper.seq_b(w_b.value, 8)
        b = InstructionMapper.seq_b(v_x, 8)
        temp = InstructionMapper.binary_op(a, b, 'AND')
        instance.initial_regs[reg_a] = U64(InstructionMapper.inverse_seq_b(temp))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def xor_imm(instance, arg):
        print(f"xor_imm ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        a = InstructionMapper.seq_b(w_b.value, 8)
        b = InstructionMapper.seq_b(v_x, 8)
        temp = InstructionMapper.binary_op(a, b, 'XOR')
        instance.initial_regs[reg_a] = U64(InstructionMapper.inverse_seq_b(temp))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def or_imm(instance, arg):
        print(f"or_imm ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        a = InstructionMapper.seq_b(w_b.value, 8)
        b = InstructionMapper.seq_b(v_x, 8)
        temp = InstructionMapper.binary_op(a, b, 'OR')
        instance.initial_regs[reg_a] = U64(InstructionMapper.inverse_seq_b(temp))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def mul_imm_32(instance, arg):
        print(f"mul_imm_32 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        instance.initial_regs[reg_a] = InstructionMapper.signed_ext((w_b * v_x) % 2 ** 32, 4)
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def mul_imm_64(instance, arg):
        print(f"mul_imm_64 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        instance.initial_regs[reg_a] = (w_b * v_x) % 2 ** 64
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def set_lt_unsigned_imm(instance, arg):
        print(f"set_lt_unsigned_imm ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        instance.initial_regs[reg_a] = U64(w_b < v_x)
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def set_lt_signed_imm(instance, arg):
        print(f"set_lt_signed_imm ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        instance.initial_regs[reg_a] = U64(InstructionMapper.signed_z(w_b, 8) < InstructionMapper.signed_z(v_x, 8))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def shlo_l_imm_32(instance, arg):
        print(f"shlo_l_imm_32 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = w_b * 2 ** (v_x % 32)
        instance.initial_regs[reg_a] = U64(InstructionMapper.signed_ext(temp % 2 ** 32, 4))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def shlo_l_imm_64(instance, arg):
        print(f"shlo_l_imm_64 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = w_b * 2 ** (v_x % 64)
        instance.initial_regs[reg_a] = U64(InstructionMapper.signed_ext(temp % 2 ** 64, 8))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def shlo_r_imm_32(instance, arg):
        print(f" shlo_r_imm_32 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        temp = (w_b % 2 ** 32) // (2 ** (v_x % 32))
        instance.initial_regs[reg_a] = InstructionMapper.signed_ext(temp, 4)
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def shlo_r_imm_64(instance, arg):
        print(f" shlo_r_imm_64 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        temp = w_b // (2 ** (v_x % 32))
        instance.initial_regs[reg_a] = InstructionMapper.signed_ext(temp, 8)
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def shar_r_imm_32(instance, arg):
        print(f" shar_r_imm_32 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        temp = (InstructionMapper.signed_z(w_b % 2 ** 32, 4)) // 2 ** (v_x % 32)
        instance.initial_regs[reg_a] = U64(InstructionMapper.inverse_signed_z(temp, 8))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def shar_r_imm_64(instance, arg):
        print(f" shar_r_imm_64")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        temp = InstructionMapper.signed_z(w_b, 8) // (1 << (v_x % 64))
        instance.initial_regs[reg_a] = U64(InstructionMapper.inverse_signed_z(temp, 8))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def neg_add_imm_32(instance, arg):
        print(f"neg_add_imm_32")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = v_x + 2 ** 32 - w_b
        instance.initial_regs[reg_a] = U64(InstructionMapper.signed_ext(temp % 2 ** 32, 4))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def neg_add_imm_64(instance, arg):
        print(f"neg_add_imm_64 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = v_x + 2 ** 64 - w_b
        instance.initial_regs[reg_a] = U64(temp % 2 ** 64)
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def set_gt_unsigned_imm(instance, arg):
        print(f"set_gt_unsigned_imm")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        instance.initial_regs[reg_a] = U64(w_b > v_x)
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def set_gt_signed_imm(instance, arg):
        print(f"set_gt_signed_imm ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        instance.initial_regs[reg_a] = U64(InstructionMapper.signed_z(w_b, 8) > InstructionMapper.signed_z(v_x, 8))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def shlo_r_imm_alt_32(instance, arg):
        print(f" shlo_r_imm_alt_32 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = (v_x % 2 ** 32) // 2 ** (w_b % 32)
        instance.initial_regs[reg_a] = U64(InstructionMapper.signed_ext(temp, 4))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def shlo_r_imm_alt_64(instance, arg):
        print(f" shlo_r_imm_alt_64 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = v_x // 2 ** (w_b % 64)
        instance.initial_regs[reg_a] = U64(temp)
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def shar_r_imm_alt_32(instance, arg):
        print(f" shar_r_imm_alt_32 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = InstructionMapper.signed_z(v_x % 2 ** 32, 4) // 2 ** (w_b % 32)
        instance.initial_regs[reg_a] = U64(InstructionMapper.inverse_signed_z(temp, 8))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def shar_r_imm_alt_64(instance, arg):
        print(f" shar_r_imm_alt_64 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = InstructionMapper.signed_z(v_x, 8) // 2 ** (w_b % 64)
        instance.initial_regs[reg_a] = U64(InstructionMapper.inverse_signed_z(math.floor(temp), 8))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def shlo_l_imm_alt_32(instance, arg):
        print(f"shlo_l_imm_alt_32 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = (v_x * 2 ** (w_b % 32)) % 2 ** 32
        instance.initial_regs[reg_a] = U64(InstructionMapper.signed_ext(temp, 4))
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def shlo_l_imm_alt_64(instance, arg):
        print(f"shlo_l_imm_alt_64")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = (v_x * 2 ** (w_b % 64)) % 2 ** 64
        instance.initial_regs[reg_a] = U64(temp)
        InstructionMapper.increase_counter(instance, len(arg) + 1)

    @staticmethod
    def cmov_iz_imm(instance, arg):
        print(f"cmov_iz_imm")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        if w_b == 0:
            instance.initial_regs[reg_a] = U64(v_x)
        else:
            instance.initial_regs[reg_a] = U64(w_a)

    @staticmethod
    def cmov_nz_imm(instance, arg):
        print(f"cmov_nz_imm")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        w_a = int(InstructionMapper.reg_value(instance, reg_a))
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        if w_b != 0:
            instance.initial_regs[reg_a] = U64(v_x)
        else:
            instance.initial_regs[reg_a] = U64(w_a)

    @staticmethod
    def rot_r_imm_32(instance, arg):
        print(f"rot_r_imm_32")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = InstructionMapper.right_rot(InstructionMapper.seq_b(w_b, 4), v_x)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_a] = U64(InstructionMapper.signed_ext(InstructionMapper.inverse_seq_b(temp), 4))

    @staticmethod
    def rot_r_imm_alt_32(instance, arg):
        print(f"rot_r_imm_alt_32 ")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = InstructionMapper.right_rot(InstructionMapper.seq_b(v_x, 4), w_b)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_a] = U64(InstructionMapper.signed_ext(InstructionMapper.inverse_seq_b(temp), 4))

    @staticmethod
    def rot_r_imm_64(instance, arg):
        print(f"rot_r_imm_64")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = InstructionMapper.right_rot(InstructionMapper.seq_b(w_b, 8), v_x)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_a] = U64(InstructionMapper.inverse_seq_b(temp))

    @staticmethod
    def rot_r_imm_alt_64(instance, arg):
        print(f"rot_r_imm_alt_64")
        reg_a, reg_b, l_x, v_x = InstructionMapper.reg_reg_imm(arg)
        w_b = int(InstructionMapper.reg_value(instance, reg_b))
        temp = InstructionMapper.right_rot(InstructionMapper.seq_b(v_x, 8), w_b)
        InstructionMapper.increase_counter(instance, len(arg) + 1)
        instance.initial_regs[reg_a] = U64(InstructionMapper.inverse_seq_b(temp))

    @staticmethod
    def branch_eq(instance, arg):
        print("branch_eq")
        reg_a, reg_b, v_x = InstructionMapper.reg_reg_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_x, w_a == w_b)
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_ne(instance, arg):
        print("branch_ne")
        reg_a, reg_b, v_x = InstructionMapper.reg_reg_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_x, w_a != w_b)
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_lt_u(instance, arg):
        print("branch_lt_u")
        reg_a, reg_b, v_x = InstructionMapper.reg_reg_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_x, w_a < w_b)
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_lt_s(instance, arg):
        print("branch_lt_s")
        reg_a, reg_b, v_x = InstructionMapper.reg_reg_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_x,InstructionMapper.signed_z(w_a, 8) <InstructionMapper.signed_z(w_b, 8))
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_ge_u(instance, arg):
        print("branch_ge_u")
        reg_a, reg_b, v_x = InstructionMapper.reg_reg_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_x, w_a >= w_b)
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def branch_ge_s(instance, arg):
        print("branch_ge_s")
        reg_a, reg_b, v_x = InstructionMapper.reg_reg_off(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        w_b = InstructionMapper.reg_value(instance, reg_b)
        InstructionMapper.increase_counter(instance, len(arg) + 2)
        result = InstructionMapper.branch(instance, v_x,InstructionMapper.signed_z(w_a, 8) >= InstructionMapper.signed_z(w_b, 8))
        if result["status"] == "continue":
            return result["value"]
        else:
            return "panic"

    @staticmethod
    def store_imm_ind_u8(instance, arg):
        print("store_imm_u8")
        reg_a, l_x, l_y, v_x, v_y = InstructionMapper.reg_imm_imm(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        address = w_a + v_x
        content = [v_y % 2 ** 8]
        if InstructionMapper.valid_address(instance.initial_memory, address, True):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, address, content)
        else:
            return "page-fault"

    @staticmethod
    def store_imm_ind_u16(instance, arg):
        print("store_imm_ind_u16")
        reg_a, l_x, l_y, v_x, v_y = InstructionMapper.reg_imm_imm(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        address = w_a + v_x
        serialize = IntegerCodec(2)
        buffer = bytearray(2)
        IntegerCodec.encode_into(serialize, v_y % 2 ** 16, buffer)
        content = list(buffer.rstrip(b'\x00'))
        if InstructionMapper.valid_address(instance.initial_memory, U32(address), 2, True):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            content = InstructionMapper.extend_array(content, 2)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, address, content)
        else:
            return "page-fault"

    @staticmethod
    def store_imm_ind_u32(instance, arg):
        print("store_imm_ind_u32")
        reg_a, l_x, l_y, v_x, v_y = InstructionMapper.reg_imm_imm(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        address = w_a + v_x
        serialize = IntegerCodec(4)
        buffer = bytearray(4)
        IntegerCodec.encode_into(serialize, v_y % 2 ** 32, buffer)
        content = list(buffer.rstrip(b'\x00'))
        if InstructionMapper.valid_address(instance.initial_memory, address, 4, True):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            content = InstructionMapper.extend_array(content, 4)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, address, content)
        else:
            return "page-fault"

    @staticmethod
    def store_imm_ind_u64(instance, arg):
        print("store_imm_ind_u64")
        reg_a, l_x, l_y, v_x, v_y = InstructionMapper.reg_imm_imm(arg)
        w_a = InstructionMapper.reg_value(instance, reg_a)
        address = w_a + v_x
        serialize = IntegerCodec(8)
        buffer = bytearray(8)
        IntegerCodec.encode_into(serialize, v_y, buffer)
        content = list(buffer.rstrip(b'\x00'))
        if InstructionMapper.valid_address(instance.initial_memory, address, 8, True):
            InstructionMapper.increase_counter(instance, len(arg) + 1)
            content = InstructionMapper.extend_array(content, 8)
            instance.initial_memory = InstructionMapper.store_value(instance.initial_memory, address, content)
        else:
            return "page-fault"



