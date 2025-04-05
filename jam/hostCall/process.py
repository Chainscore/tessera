# import json
# from jam.types.base.sequences.bytes.bytes import Bytes
# from hashlib import blake2b
# import os
# from jam.utils.codec.primitives.integers import IntegerCodec
# from jam.types.base.integers.fixed import U32, U64, U256
# from jam.services import historicalLookup
# from jam.pvm.opcode_mapping import InstructionMapper
# from jam.pvm.extract import Execution
# from jam.pvm.program import Program
# from jam.types.base.dictionary import DictionaryCodec
# import copy
# from jam.pvm.register import Registers
# from jam.pvm.pvm_memory import PageMemory
# from jam.types.protocol.core import Balance, Gas, ServiceId
# from jam.state.components.delta import AccountData, Delta
# from jam.hostCall.types import XContent, RefineMap, Segment
# from jam.types.work.package import WorkPackage
# from typing import Optional
# from jam.pvm.extract import Status


# class HostCall:
#     def __init__(self,
#                  register: Registers,
#                  memory: PageMemory,
#                  gas: Gas,
#                  service: Optional[AccountData] = None,
#                  s_index: Optional[U32] = None,
#                  delta: Optional[Delta] = None,
#                  xcontext: Optional[XContent] = None,
#                  ycontext: Optional[XContent] = None,
#                  refine: Optional[RefineMap] = None,
#                  export: Optional[Segment] = None,
#                  e_index: Optional[U32] = None,
#                  timeslot: Optional[U32] = None,
#                  work_package: Optional[WorkPackage] = None,
#                  blob: Optional[Bytes] = None,
#                  segment: Optional[Segment] = None
#                  ):
#         self.initial_regs = register
#         self.initial_memory = memory
#         self.initial_gas = gas
#         self.initial_service_account = service
#         self.initial_service_index = s_index
#         self.initial_delta = delta
#         self.initial_xcontent_x = xcontext
#         self.initial_xcontent_y = ycontext
#         self.initial_refine_map = refine
#         self.initial_export_segment = export
#         self.initial_export_segment_index = e_index
#         self.initial_timeslot = timeslot
#         self.initial_work_package = work_package
#         self.initial_blob = blob
#         self.segment_vec = segment

#         self.function_mapping = {
#             0: self.gas(),
#             1: self.lookup(),
#             2: self.read(),
#             3: self.write(),
#             4: self.info(),
#             5: self.bless(),
#             6: self.assign(),
#             7: self.designate(),
#             8: self.checkpoint(),
#             9: self.new(),
#             10: self.upgrade(),
#             11: self.transfer(),
#             12: self.eject(),
#             13: self.query(),
#             14: self.solicit(),
#             15: self.forget(),
#             16: self._yield(),
#             17: self.historical_lookup(),
#             18: self.fetch(),
#             19: self.export(),
#             20: self.machine(),
#             21: self.peek(),
#             22: self.poke(),
#             23: self.zero(),
#             24: self.void(),
#             25: self.invoke(),
#             26: self.expunge(),
#         }

#     def call_function_by_number(self, number):
#         func = self.function_mapping.get(number)
#         if func:
#             return func()
#         else:
#             return f"Invalid number: {number}. Please provide a number between 1 and 12."

#     @staticmethod
#     def get_keys(d, is_string=False):
#         keys = set()
#         for key in d.keys():
#             try:
#                 if not is_string:
#                     numeric_key = int(key)
#                     keys.add(numeric_key)
#                 else:
#                     keys.add(key)

#             except (ValueError, TypeError):
#                 pass
#         return keys

#     def read(self):
#         self.initial_gas -= 10
#         if self.initial_regs["7"] == 2**64 - 1:
#             _s = self.initial_service_index
#         else:
#             _s = self.initial_regs["7"]
#         delta_keys = HostCall.get_keys(self.initial_delta)
#         if self.initial_service_index == _s:
#             a = self.initial_service_account
#         elif _s in delta_keys:
#             a = self.initial_delta[str(_s)]
#         else:
#             a = None
#         k_o = self.initial_regs.get("8", 0)
#         k_z = self.initial_regs.get("9", 0)
#         o = self.initial_regs.get("10", 0)
#         serialize = IntegerCodec(4)
#         buffer = bytearray(4)
#         IntegerCodec.encode_into(serialize, _s, buffer)
#         buffer = list(buffer)
#         values = HostCall.get_values(self.initial_memory, k_o, k_z)
#         final_arr = buffer + values
#         _hex = HostCall.get_hex_string(Bytes(final_arr))
#         byte_value = bytes.fromhex(_hex[2:])  # [2:] removes "0x"
#         hashed = "0x" + blake2b(byte_value, digest_size=32).hexdigest()
#         is_p, a_s = HostCall.search_p(a["s_map"], hashed)
#         as_keys = HostCall.get_keys(a["s_map"], True)
#         if not HostCall.is_valid(self.initial_memory, k_o, k_z):
#             v = "error"
#         elif a is not None and hashed in as_keys:
#             v = a_s
#         else:
#             v = None
#         if isinstance(v, list):
#             f = min(self.initial_regs["11"], len(v))
#             _l = min(self.initial_regs.get("12", 0), len(v) - f)
#         else:
#             f = self.initial_regs.get("10", 0)
#             _l = self.initial_regs.get("11", 0)
#         if v == "error" or not HostCall.is_valid(self.initial_memory, o, _l, True):
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         elif v is None:
#             self.initial_regs["7"] = 2**64 - 1
#         else:
#             self.initial_regs["7"] = len(v)
#             self.initial_memory = HostCall.insert_values(self.initial_memory, o, v)
#         return self

#     def lookup(self):
#         self.initial_gas -= 10
#         delta_keys = HostCall.get_keys(self.initial_delta)
#         if self.initial_service_index <= self.initial_regs["7"] <= 2**64-1:
#             a = self.initial_service_account
#         elif self.initial_regs["7"] in delta_keys:
#             key = str(self.initial_regs["7"])
#             a = self.initial_delta[key]
#         else:
#             a = None
#         h = self.initial_regs.get("8", 0)
#         o = self.initial_regs.get("9", 0)

#         values = HostCall.get_values(self.initial_memory, h, 32)
#         _hex = HostCall.get_hex_string(Bytes(values))
#         byte_value = bytes.fromhex(_hex[2:])  # [2:] removes "0x"
#         hashed = "0x" + blake2b(byte_value, digest_size=32).hexdigest()

#         is_p, a_p = HostCall.search_p(a["p_map"], hashed)
#         ap_keys = HostCall.get_keys(a["p_map"], True)
#         if not HostCall.is_valid(self.initial_memory, h, 32):
#             v = "error"
#         elif a is None or hashed not in ap_keys:
#             v = None
#         else:
#             v = a_p

#         if isinstance(v, list):
#             f = min(self.initial_regs["10"], len(v))
#             _l = min(self.initial_regs.get("11", 0), len(v) - f)
#         else:
#             f = self.initial_regs.get("10", 0)
#             _l = self.initial_regs.get("11", 0)

#         if v == "error" or not HostCall.is_valid(self.initial_memory, o, _l, True):
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         elif v is None:
#             self.initial_regs["7"] = 2**64 - 1
#         else:
#             self.initial_regs["7"] = len(v)
#             self.initial_memory = HostCall.insert_values(self.initial_memory, o, v)
#         return self

#     def write(self):
#         self.initial_gas -= 10
#         k_o = self.initial_regs.get("7", 0)
#         k_z = self.initial_regs.get("8", 0)
#         v_o = self.initial_regs.get("9", 0)
#         v_z = self.initial_regs.get("10", 0)
#         values = HostCall.get_values(self.initial_memory, k_o, k_z)
#         serialize = IntegerCodec(4)
#         buffer = bytearray(4)
#         IntegerCodec.encode_into(serialize, self.initial_service_index, buffer)
#         buffer = list(buffer)
#         final_arr = buffer + values
#         _hex = HostCall.get_hex_string(Bytes(final_arr))
#         byte_value = bytes.fromhex(_hex[2:])  # [2:] removes "0x"
#         hashed = "0x" + blake2b(byte_value, digest_size=32).hexdigest()
#         if HostCall.is_valid(self.initial_memory, k_o, k_z):
#             k = hashed
#         else:
#             k = "error"

#         if v_z == 0:
#             a = HostCall.remove_key(self.initial_service_account, k)
#         elif HostCall.is_valid(self.initial_memory, v_o, v_z):
#             temp = HostCall.get_values(self.initial_memory, v_o, v_z)
#             s = copy.deepcopy(self.initial_service_account)  # Creates a deep copy
#             s["s_map"][k] = temp
#             a = s
#         else:
#             a = "error"

#         if str(k) in HostCall.get_keys(self.initial_service_account["s_map"], True):
#             _l = len(self.initial_service_account["s_map"][k])
#         else:
#             _l = 2**64 - 1

#         if k == "error" or a == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         elif a["g"] > a["balance"]:
#             self.initial_regs["7"] = 2**64 - 5
#             return self
#         else:
#             self.initial_regs["7"] = _l
#             self.initial_service_account = a
#             return self

#     def info(self):
#         self.initial_gas -= 10
#         if self.initial_regs["7"] == 2**64 - 1:
#             t = self.initial_delta[self.initial_service_index]
#         else:
#             print(self.initial_regs["7"])
#             t = self.initial_delta[str(self.initial_regs["7"])]

#         o = self.initial_regs["8"]
#         t_c = t["code_hash"]
#         t_b = U64(t["balance"])
#         t_t = U64(259)
#         t_g = U64(t["g"])
#         t_m = U64(t["m"])
#         t_i = U32(3)
#         t_l = U64(258)
#         byte_value = t_c[2:]
#         print(100000 & 0x1FF)
#         # Split into pairs of two characters (each byte)
#         byte_pairs = [byte_value[i:i + 2] for i in range(0, len(byte_value), 2)]

#         # Convert each pair from hex to decimal
#         decimal_array = [int(byte, 16) for byte in byte_pairs]
#         _l = HostCall.transform_l_map_structure(t["l_map"])
#         print(_l)
#         print(t["l_map"])
#         serialize = DictionaryCodec()
#         buffer = bytearray(1024)  # Create a buffer to store encoded data
#         serialize.encode(_l)

#         print(decimal_array)         # ✅
#         print(list(t_b.encode()))    # ✅
#         print(list(t_t.encode()))
#         print(list(t_g.encode()))    # ✅
#         print(list(t_m.encode()))    # ✅
#         print(list(t_i.encode()))
#         print(list(t_l.encode()))
#         final_array = [7] + decimal_array + list(t_b.encode()) + list(t_t.encode()) + list(t_g.encode()) + list(t_m.encode()) + list(t_i.encode()) + list(t_l.encode())
#         if t is not None:
#             m = final_array
#         else:
#             m = None

#         if m is not None and InstructionMapper.valid_address(self.initial_memory, o, len(m)):
#             InstructionMapper.store_value(self.initial_memory, o, m)

#         if not InstructionMapper.valid_address(self.initial_memory, o, len(m)):
#             self.initial_regs[6] = 2**64 - 3
#         elif m is None:
#             self.initial_regs[6] = 2 ** 64 - 1
#         else:
#             self.initial_regs[6] = 0
#         return self


#         self.initial_memory = HostCall.insert_values(self.initial_memory, o, final_array)
#         return self

#     def new(self):
#         self.initial_gas -= 10
#         o = self.initial_regs["7"]
#         _l = self.initial_regs["8"]
#         g = self.initial_regs["9"]
#         m = self.initial_regs["10"]

#         if HostCall.is_valid(self.initial_memory, o, 32):
#             values = HostCall.get_values(self.initial_memory, o, 32)
#             c = HostCall.get_hex_string(Bytes(values))
#         else:
#             c = "error"

#         if c != "error":
#             a_t = 100 + 81 + _l
#             a = {
#                 "s_map": {},
#                 "l_map": {
#                     c: {
#                         "t": [],
#                         "l": _l
#                     }
#                 },
#                 "p_map": {},
#                 "code_hash": c,
#                 "balance": a_t,
#                 "g": g,
#                 "m": m

#             }
#         else:
#             a_t = 0
#             a = "error"
#         s_i = str(self.initial_xcontent_x["S"])
#         s = copy.deepcopy(self.initial_xcontent_x["U"]["D"][s_i])
#         s_b = s["balance"] - a_t
#         s["balance"] = s["balance"] - a_t
#         temp1, temp2, s_t = HostCall.cal_t(s)
#         x_i = str(self.initial_xcontent_x["I"])

#         if c == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         elif s_b < s_t:
#             self.initial_regs["7"] = 2**64 - 7
#             return self
#         else:
#             self.initial_xcontent_x["U"]["D"][s_i] = s
#             self.initial_regs["7"] = self.initial_xcontent_x["I"]
#             self.initial_xcontent_x["U"]["D"][x_i] = a
#             keys = HostCall.get_keys(self.initial_xcontent_x["U"]["D"])
#             _i = 2**8 + ((int(x_i) - 2**8 + 42) % (2**10 - 2**9))
#             _i = HostCall.check(keys, int(_i))
#             self.initial_xcontent_x["I"] = _i
#             return self

#     def upgrade(self):
#         self.initial_gas -= 10
#         o = self.initial_regs["7"]
#         g = self.initial_regs["8"]
#         m = self.initial_regs["9"]

#         if HostCall.is_valid(self.initial_memory, o, 32):
#             values = HostCall.get_values(self.initial_memory, o, 32)
#             c = HostCall.get_hex_string(Bytes(values))
#         else:
#             c = "error"

#         if c == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         else:
#             self.initial_regs["7"] = 0
#             s_i = str(self.initial_xcontent_x["S"])
#             s = self.initial_xcontent_x["U"]["D"][s_i]
#             s["code_hash"] = c
#             s["g"] = g
#             s["m"] = m
#             return self

#     def transfer(self):
#         self.initial_gas -= 10
#         _d = self.initial_regs["7"]
#         a = self.initial_regs["8"]
#         _l = self.initial_regs["9"]
#         o = self.initial_regs["10"]

#         d = self.initial_xcontent_x["U"]["D"]
#         w_t = 128
#         s_i = self.initial_xcontent_x["S"]
#         if HostCall.is_valid(self.initial_memory, o, w_t):
#             values = HostCall.get_values(self.initial_memory, o, w_t)
#             t = {
#                 "sender_index": self.initial_xcontent_x["S"],
#                 "receiver_index": _d,
#                 "amount": a,
#                 "memo": values,
#                 "gas_limit": _l
#             }
#         else:
#             t = "error"
#         s = self.initial_xcontent_x["U"]["D"][str(s_i)]
#         b = s["balance"] - a
#         values = list(s["s_map"].values())[0]
#         temp1, temp2, s_t = HostCall.cal_t(s)
#         if len(values) > 0:
#             s_t += 32 + len(values)

#         if t == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         elif _d not in HostCall.get_keys(d):
#             self.initial_regs["7"] = 2**64 - 4
#             return self
#         elif _l < d[str(_d)]["m"]:
#             self.initial_regs["7"] = 2 ** 64 - 8
#             return self
#         elif b < s_t:
#             self.initial_regs["7"] = 2 ** 64 - 7
#             return self
#         else:
#             self.initial_regs["7"] = 0
#             self.initial_xcontent_x["T"].append(t)
#             s["balance"] = b
#             return self

#     def eject(self):
#         self.initial_gas -= 10
#         _d = self.initial_regs["7"]
#         o = self.initial_regs["8"]

#         if HostCall.is_valid(self.initial_memory, o, 32):
#             values = HostCall.get_values(self.initial_memory, o, 32)
#             h = HostCall.get_hex_string(Bytes(values))
#             # byte_value = bytes.fromhex(_hex[2:])  # [2:] removes "0x"
#             # hashed = "0x" + blake2b(byte_value, digest_size=32).hexdigest()
#         else:
#             h = "error"

#         s_i = self.initial_xcontent_x["S"]
#         if _d != s_i and _d in HostCall.get_keys(self.initial_xcontent_x["U"]["D"]):
#             d = self.initial_xcontent_x["U"]["D"][str(_d)]
#         else:
#             d = "error"

#         s = copy.deepcopy(self.initial_xcontent_x["U"]["D"][str(s_i)])
#         enc_si = U256(s_i)
#         enc_si = enc_si.encode()
#         hex_str = "0x" + enc_si.hex()
#         if h == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         elif d == "error" or d.get("code_hash", None) != hex_str:
#             self.initial_regs["7"] = 2 ** 64 - 4
#             return self
#         s["balance"] += d["balance"]
#         d_i, d_o, d_t = HostCall.cal_t(d)
#         _l = max(81, d_o) - 81
#         if d_i != 2 or h not in HostCall.get_keys(d["l_map"], True):
#             self.initial_regs["7"] = 2 ** 64 - 10
#             return self
#         elif len(d["l_map"][h]["t"]) == 2 :
#             # elif len(d["l_map"][h]["t"]) == 2 and d["l_map"][h]["t"][1] < self.initial_timeslot - 28800:
#             self.initial_regs["7"] = 0
#             D = copy.deepcopy(self.initial_xcontent_x["U"]["D"])
#             del D[str(_d)]
#             self.initial_xcontent_x["U"]["D"] = D
#             self.initial_xcontent_x["U"]["D"][str(s_i)] = s
#             return self
#         else:
#             self.initial_regs["7"] = 2 ** 64 - 10
#             return self

#     def query(self):
#         self.initial_gas -= 10
#         o = self.initial_regs["7"]
#         z = self.initial_regs["8"]

#         if HostCall.is_valid(self.initial_memory, o, 32):
#             values = HostCall.get_values(self.initial_memory, o, 32)
#             h = HostCall.get_hex_string(Bytes(values))
#         else:
#             h = "error"
#         s_i = self.initial_xcontent_x["S"]
#         _l = self.initial_xcontent_x["U"]["D"][str(s_i)]["l_map"]
#         values_l = list(_l.values())[0]
#         keys_l = list(_l.keys())[0]
#         if h == keys_l and z == values_l["l"]:
#             a = values_l["t"]
#         else:
#             a = "error"

#         if h == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         elif a == "error":
#             self.initial_regs["7"] = 2 ** 64 - 1
#             self.initial_regs["8"] = 0
#             return self
#         elif len(a) == 0:
#             self.initial_regs["7"] = 0
#             self.initial_regs["8"] = 0
#             return self
#         elif len(a) == 1:
#             self.initial_regs["7"] = 1 + 2**32 * a[0]
#             self.initial_regs["8"] = 0
#             return self
#         elif len(a) == 2:
#             self.initial_regs["7"] = 2 + 2**32 * a[0]
#             self.initial_regs["8"] = a[1]
#             return self
#         elif len(a) == 3:
#             self.initial_regs["7"] = 3 + 2**32 * a[0]
#             self.initial_regs["8"] = a[1] + 2**32 * a[2]
#             return self

#     def _yield(self):
#         self.initial_gas -= 10
#         o = self.initial_regs["7"]

#         if HostCall.is_valid(self.initial_memory, o, 32):
#             values = HostCall.get_values(self.initial_memory, o, 32)
#             h = HostCall.get_hex_string(Bytes(values))
#         else:
#             h = "error"

#         if h == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         else:
#             self.initial_regs["7"] = 0
#             self.initial_xcontent_x["Y"] = h
#             return self

#     def peek(self):
#         self.initial_gas -= 10
#         n = self.initial_regs["7"]
#         o = self.initial_regs["8"]
#         s = self.initial_regs["9"]
#         z = self.initial_regs["10"]

#         if not HostCall.is_valid(self.initial_memory, o, z):
#             return Status("halt"), self.initial_regs[6], self.initial_memory
#         elif n not in HostCall.get_keys(self.initial_refine_map):
#             self.initial_regs["7"] = 2**64 - 4
#             return Status("continue"), self.initial_regs[6], self.initial_memory
#         elif not HostCall.is_valid(self.initial_refine_map[str(n)]["U"], s, z):
#             self.initial_regs["7"] = 2**64 - 3
#             return Status("continue"), self.initial_regs[6], self.initial_memory
#         else:
#             self.initial_regs["7"] = 0
#             address = int(o/4096)
#             self.initial_memory["pages"][str(address)]["value"] = HostCall.get_values(self.initial_refine_map[str(n)]["U"], s, z)
#             return Status("continue"), self.initial_regs[6], self.initial_memory

#     def poke(self):
#         self.initial_gas -= 10
#         n = self.initial_regs["7"]
#         s = self.initial_regs["8"]
#         o = self.initial_regs["9"]
#         z = self.initial_regs["10"]

#         if not HostCall.is_valid(self.initial_memory, s, z):
#             self.initial_regs["7"] = 2 ** 64 - 3
#             return Status("halt"), self.initial_regs[6], self.initial_refine_map
#         elif n not in HostCall.get_keys(self.initial_refine_map):
#             self.initial_regs["7"] = 2 ** 64 - 4
#             return Status("continue"), self.initial_regs[6], self.initial_refine_map
#         elif not HostCall.is_valid(self.initial_refine_map[str(n)]["U"], o, z):
#             print("OOB")
#             self.initial_regs["7"] = 2 ** 64 - 3
#             return Status("continue"), self.initial_regs[6], self.initial_refine_map
#         else:
#             self.initial_regs["7"] = 0
#             address = int(o / 4096)
#             self.initial_refine_map[str(n)]["U"]["pages"][str(address)]["value"] = HostCall.get_values(self.initial_memory, s, z)
#             return Status("continue"), self.initial_regs[6], self.initial_refine_map

#     def zero(self):
#         self.initial_gas -= 10
#         n = self.initial_regs["7"]
#         p = self.initial_regs["8"]
#         c = self.initial_regs["9"]

#         if n in HostCall.get_keys(self.initial_refine_map):
#             u = copy.deepcopy(self.initial_refine_map[str(n)]["U"])
#         else:
#             u = "error"
#         address = int((p * 2**12)/4096)

#         if p < 16 or p+c >= (2**32 / 2**12):
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         elif u == "error":
#             self.initial_regs["7"] = 2**64 - 4
#             return self
#         if str(address) in HostCall.get_keys(u["pages"], True):
#             u["pages"][str(address)]["value"] = []
#             u["pages"][str(address)]["access"] = {
#                 "inaccessible": False,
#                 "writable": True,
#                 "readable": False
#             }
#             self.initial_refine_map[str(n)]["U"] = u
#         return self

#     def void(self):
#         self.initial_gas -= 10
#         n = self.initial_regs["7"]
#         p = self.initial_regs["8"]
#         c = self.initial_regs["9"]

#         if n in HostCall.get_keys(self.initial_refine_map):
#             u = copy.deepcopy(self.initial_refine_map[str(n)]["U"])
#         else:
#             u = "error"
#         address = int((p * 2**12)/4096)

#         if u == "error":
#             self.initial_regs["7"] = 2 ** 64 - 4
#             return self

#         if str(address) in HostCall.get_keys(u["pages"], True):
#             u["pages"][str(address)]["value"] = []
#             u["pages"][str(address)]["access"] = {
#                 "inaccessible": True,
#                 "writable": False,
#                 "readable": False
#             }
#             if p < 16 or p + c >= (2 ** 32 / 2 ** 12) or self.initial_refine_map[str(n)]["U"]["pages"][str(address)]["access"]["inaccessible"]:
#                 self.initial_regs["7"] = 2 ** 64 - 3
#             else:
#                 self.initial_regs["7"] = 0
#                 self.initial_refine_map[str(n)]["U"] = u
#         return self

#     def solicit(self):
#         self.initial_gas -= 10
#         o = self.initial_regs["7"]
#         z = self.initial_regs["8"]
#         if HostCall.is_valid(self.initial_memory, o, 32):
#             values = HostCall.get_values(self.initial_memory, o, 32)
#             h = HostCall.get_hex_string(Bytes(values))
#             print(h)
#         else:
#             h = "error"

#         s_i = self.initial_xcontent_x["S"]
#         s = copy.deepcopy(self.initial_xcontent_x["U"]["D"][str(s_i)])
#         _l = s["l_map"]
#         if h != "error" and h not in HostCall.get_keys(_l, True):
#             print("one")
#             _l[h] = {
#                 "t": [],
#                 "l": z
#             }
#             a = s
#         elif h in HostCall.get_keys(_l, True) and len(_l[h].get("t", [])) == 2:
#             print("two")
#             _l[h]["t"].append(self.initial_timeslot)
#             a = s
#         else:
#             print("three")
#             a = "error"
#         a_i, a_o, a_t = HostCall.cal_t(a)
#         if h == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         elif a == "error":
#             self.initial_regs["7"] = 2 ** 64 - 10
#             return self
#         elif a["balance"] < a_t:
#             self.initial_regs["7"] = 2 ** 64 - 5
#             return self
#         else:
#             self.initial_regs["7"] = 0
#             self.initial_xcontent_x["U"]["D"][str(s_i)] = a
#             return self

#     def forget(self):
#         self.initial_gas -= 10
#         o = self.initial_regs["7"]
#         z = self.initial_regs["8"]

#         if HostCall.is_valid(self.initial_memory, o, 32):
#             values = HostCall.get_values(self.initial_memory, o, 32)
#             h = HostCall.get_hex_string(Bytes(values))
#         else:
#             h = "error"
#         s_i = self.initial_xcontent_x["S"]
#         x_s = self.initial_xcontent_x["U"]["D"][str(s_i)]
#         a = copy.deepcopy(x_s)
#         t = x_s["l_map"].get(h, {}).get("t", None)
#         _l = a["l_map"]
#         p_map = a["p_map"]

#         if t is not None and (len(t) == 0 or (len(t) == 2 and t[1] < self.initial_timeslot - 28800)):
#             print("one")
#             print(h, type(h))
#             del _l[h]
#             byte_value = bytes.fromhex(h[2:])  # [2:] removes "0x"
#             hashed = "0x" + blake2b(byte_value, digest_size=32).hexdigest()
#             del p_map[hashed]
#         elif t is not None and len(t) == 1:
#             print("two")
#             _l[h]["t"] = [t[0], self.initial_timeslot]
#         elif t is not None and len(t) == 3:
#             print("three")
#             _l[h]["t"] = [t[2], self.initial_timeslot]
#         else:
#             print("four")
#             a = "error"

#         if h == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         elif a == "error":
#             self.initial_regs["7"] = 2 ** 64 - 10
#             return self
#         else:
#             self.initial_regs["7"] = 0
#             self.initial_xcontent_x["U"]["D"][str(s_i)] = a
#             return self

#     def historical_lookup(self):
#         self.initial_gas -= 10
#         w_a = self.initial_regs["7"]
#         h = self.initial_regs["8"]
#         o = self.initial_regs["9"]
#         s_i = self.initial_service_index
#         d = self.initial_delta
#         d_keys = HostCall.get_keys(d)
#         if w_a == 2**64 - 1 and s_i in d_keys:
#             a = d[str(s_i)]
#         elif w_a in d_keys:
#             a = d[str(w_a)]
#         else:
#             a = None

#         if not HostCall.is_valid(self.initial_memory, h, 32):
#             v = "error"
#         elif a is None:
#             v = None
#         else:
#             values = HostCall.get_values(self.initial_memory, h, 32)
#             h = HostCall.get_hex_string(Bytes(values))
#             v = historicalLookup.historical_look_up(a, self.initial_timeslot, h)
#         v_len = len(v) if v is not None else 0
#         f = min(self.initial_regs.get("10", 0), v_len)
#         _l = min(self.initial_regs.get("11", 0), v_len - f)
#         if v == "error" or not HostCall.is_valid(self.initial_memory, o, _l):
#             self.initial_regs["7"] = 2**64 - 3
#             return Status("panic"), self.initial_regs[6], self.initial_memory
#         elif v is None:
#             self.initial_regs["7"] = 2 ** 64 - 1
#             return Status("continue"), self.initial_regs[6], self.initial_memory
#         else:
#             self.initial_regs["7"] = len(v)
#             self.initial_memory = HostCall.insert_values(self.initial_memory, o, v)
#             return Status("continue"), self.initial_regs[6], self.initial_memory

#     def export(self):
#         self.initial_gas -= 10
#         p = self.initial_regs["7"]
#         z = min(self.initial_regs["8"], 4104)
#         if HostCall.is_valid(self.initial_memory, p, z):
#             print("one")
#             values = HostCall.get_values(self.initial_memory, p, z)
#             print(values)
#             x = HostCall.pad_zero(values, 24)
#             print(x)
#         else:
#             x = "error"

#         if x == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return Status("panic"), self.initial_regs[6], self.initial_export_segment
#         elif self.initial_export_segment_index + len(self.initial_export_segment) >= 2**11:
#             self.initial_regs["7"] = 2 ** 64 - 5
#             return Status("continue"), self.initial_regs[6], self.initial_export_segment
#         else:
#             self.initial_regs["7"] = self.initial_export_segment_index + len(self.initial_export_segment)
#             self.initial_export_segment.append(x)
#             return Status("continue"), self.initial_regs[6], self.initial_export_segment

#     def machine(self):
#         self.initial_gas -= 10
#         p_o = self.initial_regs["7"]
#         p_z = self.initial_regs["8"]
#         i = self.initial_regs["9"]
#         if HostCall.is_valid(self.initial_memory, p_o, p_z):
#             print("one")
#             p = HostCall.get_values(self.initial_memory, p_o, p_z)
#         else:
#             p = "error"
#         m_keys =HostCall.get_keys(self.initial_refine_map, True)
#         numbers = {int(x) for x in m_keys if x.isdigit()}

#         # Start checking from 1 (smallest natural number)
#         n = 1
#         while n in numbers:
#             n += 1

#         u = {
#             "P": p,
#             "U": {
#                 "pages": {}
#             },
#             "I": i
#         }

#         if p == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return Status("halt"), self.initial_regs[6], self.initial_refine_map
#         elif Program.decode_from(p) == "Error":
#             self.initial_regs["7"] = 2 ** 64 - 10
#             return Status("continue"), self.initial_regs[6], self.initial_refine_map
#         else:
#             self.initial_regs["7"] = n
#             self.initial_refine_map[str(n)] = u
#             Status("continue"), self.initial_regs[6], self.initial_refine_map

#     def expunge(self):
#         self.initial_gas -= 10
#         n = self.initial_regs["7"]
#         if str(n) not in HostCall.get_keys(self.initial_refine_map, True):
#             self.initial_regs["7"] = 2**64 - 4
#         else:
#             self.initial_regs["7"] = self.initial_refine_map[str(n)]["I"]
#             del self.initial_refine_map[str(n)]
#         return self

#     def checkpoint(self):
#         self.initial_gas -= 10
#         self.initial_xcontent_y = self.initial_xcontent_x
#         self.initial_regs["7"] = self.initial_gas
#         return self

#     def gas(self):
#         self.initial_gas -= 10
#         self.initial_regs["7"] = self.initial_gas
#         return self

#     def bless(self):
#         m = self.initial_regs.get("7", None)
#         a = self.initial_regs.get("8", None)
#         v = self.initial_regs.get("9", None)
#         o = self.initial_regs.get("10", None)
#         n = self.initial_regs.get("11", None)
#         if HostCall.is_valid(self.initial_memory, o, 12*n):
#             c = {}
#             for i in range(80):
#                 values = HostCall.get_values(self.initial_memory, o + 12*i, 12)
#                 s_arr = values[:4]
#                 g_arr = values[-8:]
#                 s = IntegerCodec.decode_from(4, s_arr)[0]
#                 g = IntegerCodec.decode_from(8, g_arr)[0]
#                 c[s] = g
#         else:
#             c = "error"
#         s_keys = HostCall.get_keys(self.initial_xcontent_x["U"]["D"], True)
#         if c == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         elif str(m) in s_keys and str(a) in s_keys and str(v) in s_keys:
#             self.initial_regs["7"] = 2**64 - 4
#             return self
#         else:
#             self.initial_regs["7"] = 0
#             self.initial_xcontent_x["U"]["X"] = {
#                 "chi_m": m,
#                 "chi_a": a,
#                 "chi_v": v,
#                 "chi_g": c
#             }
#             return self

#     def assign(self):
#         o = self.initial_regs["7"]

#         if HostCall.is_valid(self.initial_memory, o, 32*80):
#             c = []
#             for i in range(80):
#                 values = HostCall.get_values(self.initial_memory, o + 32*i, 32)
#                 temp = HostCall.get_hex_string(Bytes(values))
#                 c.append(temp)
#         else:
#             c = "error"

#         if c == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         elif self.initial_regs["7"] >= 341:
#             self.initial_regs["7"] = 2**64 - 6
#             return self
#         else:
#             self.initial_regs["7"] = 0
#             self.initial_xcontent_x["U"]["Q"][self.initial_regs["7"]] = c
#             return self

#     def designate(self):
#         o = self.initial_regs["7"]

#         if HostCall.is_valid(self.initial_memory, o, 336*1023):
#             v = []
#             for i in range(1023):
#                 values = HostCall.get_values(self.initial_memory, o + 336 * i, 336)
#                 temp = HostCall.get_hex_string(Bytes(values))
#                 v.append(temp)
#         else:
#             v = "error"

#         if v == "error":
#             self.initial_regs["7"] = 2**64 - 3
#             return self
#         else:
#             self.initial_regs["7"] = 0
#             self.initial_xcontent_x["U"]["I"] = v
#             return self

#     def invoke(self):
#         print("invoke")
#         n = self.initial_regs[6]
#         o = self.initial_regs[7]
#         if InstructionMapper.valid_address(self.initial_memory, o, 112):
#             values = InstructionMapper.memory_value(self.initial_memory, o, 112)
#             g_arr = values[:4]
#             g = IntegerCodec.decode_from(8, bytes(g_arr))[0]
#             w = [
#                 IntegerCodec.decode_from(8, bytes(values[i:i + 8]))[0]
#                 for i in range(8, 112, 8)
#             ]
#         else:
#             g = None
#             w = None
#         p = Program.from_json(self.initial_refine_map[n].blob)
#         pvm_execution = Execution(self.initial_refine_map[n].i, g, w, self.initial_refine_map[n].memory, p)
#         c, _i, _g, _w, _u = pvm_execution.process_program()
#         serialize = IntegerCodec(8)
#         buffer = bytearray(8)
#         IntegerCodec.encode_into(serialize, _g, buffer)
#         contents = list(buffer.rstrip(b'\x00'))
#         for it in _w:
#             serialize = IntegerCodec(8)
#             buffer = bytearray(8)
#             IntegerCodec.encode_into(serialize, _g, buffer)
#             temp = list(buffer.rstrip(b'\x00'))
#             contents += temp
#         memory = copy.deepcopy(self.initial_memory)
#         refine_map = copy.deepcopy(self.initial_refine_map)
#         InstructionMapper.store_value(memory, o, contents)
#         refine_map[n].memory = _u
#         if c == "host-call":
#             refine_map[n].i = _i + 1
#         else:
#             refine_map[n].i = _i

#         if g is None:
#             self.initial_regs[6] = 2**64 - 3
#         elif n not in self.initial_refine_map.keys():
#             self.initial_regs[6] = 2**64 - 4
#         elif c == "host-call":
#             self.initial_regs[6] = 3
#             self.initial_memory = memory
#             self.initial_refine_map = refine_map
#         elif c == "out-of-gas":
#             self.initial_regs[6] = 4
#             self.initial_memory = memory
#             self.initial_refine_map = refine_map
#         elif c == "panic":
#             self.initial_regs[6] = 1
#             self.initial_memory = memory
#             self.initial_refine_map = refine_map
#         elif c == "halt":
#             self.initial_regs[6] = 0
#             self.initial_memory = memory
#             self.initial_refine_map = refine_map
#         return self

#     def fetch(self):
#         print("fetch")
#         if self.initial_regs[9] == 0:
#             serialize = DictionaryCodec()
#             v = DictionaryCodec.encode(serialize, self.initial_work_package)
#         elif self.initial_regs[9] == 1:
#             v = self.initial_blob
#         elif self.initial_regs[9] == 2 and self.initial_regs[10] < len(self.initial_work_package.items):
#             v = self.initial_work_package.items[self.initial_regs[10]].payload
#         elif self.initial_regs[9] == 3 and self.initial_regs[10] < len(self.initial_work_package.items[self.initial_regs[10]].extrinsic):
#             v = "" #implement from here

#     @staticmethod
#     def is_valid(data, address, length, writable=False):
#         page_key = str(address // 4096)
#         pages = data.get("pages", {})
#         if page_key in pages:
#             page = pages[page_key]
#             # if len(page.get("value", [])) >= length:
#             access = page.get("access", {})
#             if writable:
#                 if access.get("inaccessible", True) is False and access.get("writable", True) is True:
#                     return True
#             else:
#                 if access.get("inaccessible", True) is False:
#                     return True
#         return False

#     @staticmethod
#     def cal_t(s):
#         if s == "error":
#             return 0, 0, 0
#         l_key = HostCall.get_keys(s["l_map"], True)
#         s_key = HostCall.get_keys(s["s_map"], True)
#         a_i = 2 * len(l_key) + len(s_key)
#         a_s = 0
#         a_l = 0
#         if l_key:
#             for key in l_key:
#                 a_l += 81 + s["l_map"][key]["l"]
#         if s_key:
#             for key in s_key:
#                 a_s += 32 + len(s["s_map"][key])
#         a_o = a_l + a_s
#         a_t = 100 + 10 * a_i + a_o
#         return a_i, a_o, a_t

#     @staticmethod
#     def pad_zero(x, n):
#         len_x = len(x)
#         padding_needed = (n - (len_x % n)) % n  # Compute required padding
#         return x + [0] * padding_needed  # Append zero bytes

#     @staticmethod
#     def transform_l_map_structure(l_map):
#         transformed_data = {}

#         for key, value in l_map.items():
#             tuple_key = (key, value["l"])  # Keep the key as a string and pair it with 'l'
#             transformed_data[tuple_key] = value["t"]

#         return transformed_data

#     @staticmethod
#     def get_values(memory, h, length):
#         page_key = str(h // 4096)
#         pages = memory.get("pages", {})
#         if page_key in pages:
#             value_array = pages[page_key].get("value", [])
#             if len(value_array) >= length:
#                 return value_array[:length]
#             else:
#                 return value_array + [0] * (length - len(value_array))
#         return []

#     @staticmethod
#     def get_hex_string(byte_arr):
#         # Convert each byte to a 2-digit hex and concatenate
#         hex_str = '0x' + ''.join(format(int(b), '02x') for b in byte_arr)
#         return hex_str

#     @staticmethod
#     def search_p(p_map, search_str):
#         if search_str in p_map:
#             return True, p_map[search_str]
#         else:
#             return False, None

#     @staticmethod
#     def insert_values(memory, h, arr):
#         page_key = str(h // 4096)
#         if "pages" not in memory:
#             memory["pages"] = {}
#             # Get or initialize the page dictionary
#         page = memory["pages"].get(page_key, {})
#         page["value"] = arr  # Insert array into 'value' key

#         # Update memory
#         memory["pages"][page_key] = page
#         return memory

#     @staticmethod
#     def remove_key(data: dict, key: str) -> dict:
#         if "s_map" in data and key in data["s_map"]:
#             del data["s_map"][key]
#         return data

#     @staticmethod
#     def check(keys, i):
#         keys = {int(k) for k in keys}  # Convert all keys to integers
#         if i not in keys:
#             return i
#         else:
#             return HostCall.check(keys, (i - 2**8 + 1) % (2**10 - 2**9) + 2**8)


# def extract_json(prefix: str):
#     folder_path = "../../tests/unit/hostCall/data/export"
#     all_files = sorted(os.listdir(folder_path))
#     total_tests = 0
#     passed_tests = 0
#     selected_files = [file_name for file_name in all_files if file_name.startswith(prefix)]
#     for file_name in selected_files:
#         full_path = os.path.join(folder_path, file_name)
#         if total_tests - passed_tests >= 1:
#             break
#         with open(full_path, 'r') as file:
#             data = json.load(file)
#             host_obj = HostCall(data)
#             data = host_obj.export()
#             if data.initial_regs == data.expected_regs and data.initial_xcontent_x == data.expected_xcontent_x and data.initial_memory == data.expected_memory and data.initial_export_segment == data.expected_export_segment and data.initial_refine_map == data.expected_refine_map:
#                 print(f"✅✅✅✅✅ Test case PASSED: {file_name}")
#             else:
#                 print(f"❌❌❌❌❌ Test case FAILED: {file_name}")
#                 print(f"Initial_regs: {data.initial_regs} | Expected regs: {data.expected_regs}")
#                 print(f"Initial memory: {data.initial_memory} | Expected memory: {data.expected_memory}")
#                 print(f"Initial_x:{data.initial_xcontent_x}")
#                 print(f"Expected x:{data.expected_xcontent_x}")
#                 print(f"Initial export:{data.initial_export_segment}")
#                 print(f"Expected export:{data.expected_export_segment}")
#                 print(f"Initial refine:{data.initial_refine_map}")
#                 print(f"Expected refine:{data.expected_refine_map}")


# extract_json('host')
