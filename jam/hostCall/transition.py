from dataclasses import dataclass

from jam.accumulation.types import StateContext
from jam.types.base.dictionary import Dictionary
from jam.types.base.sequences.bytes import ByteArray32, Byte, Bytes
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.state.delta import Timestamps
from jam.types.state.delta import Delta, AccountData, AccountStorage, PreImageLookup, LookupTimestamps, LookupTable, BlobLength
from jam.types.protocol.core import Balance, Gas, ServiceId
from jam.types.base.sequences.bytes.bytes import ByteVector32
from jam.pvm.register import Registers, Register
from jam.pvm.pvm_memory import PageMemory, Memory, Access
from jam.types.base.integers.fixed import U32, U64
from jam.types.base.boolean import Boolean
from jam.utils.constants import REGISTER_COUNT
from jam.types.state.phi import Phi
from jam.types.state.chi import Chi
from jam.hostCall.types import XContent, DeferredTransfers
from jam.hostCall.types import RefineMap
from jam.hostCall.types import BoldM
from jam.types.state.iota import Iota
ServiceCodeHash = ByteArray32


@decodable_dataclass
@dataclass
class HostTransition(Codable):

    @staticmethod
    def transit(data):
        print("testing", data.initial_refine_map)
        initial_regs = HostTransition.reg_transition(data.initial_regs)
        initial_memory = HostTransition.memory_transition(data.initial_memory)
        initial_service_account = HostTransition.service_transition(data.initial_service_account)
        initial_delta = HostTransition.delta_transition(data.initial_delta)
        initial_xcontent_x = HostTransition.xcontent_transition(data.initial_xcontent_x)
        initial_refine_map = HostTransition.refine_map_transition(data.initial_refine_map)
        return initial_regs, initial_memory, initial_service_account, initial_delta, initial_xcontent_x, initial_refine_map

    @staticmethod
    def reg_transition(regs):
        initial_regs = Registers([Register(value=0) for _ in range(REGISTER_COUNT)])
        for key, value in regs.items():
            index = int(str(key))  # Convert string key to integer index
            initial_regs[index] = value  # Assign the U64 value
        return initial_regs

    @staticmethod
    def memory_transition(json_page_memory):
        PAGE_SIZE = 4096
        converted_pages = {}
        for key, memory in json_page_memory.pages.items():
            page_number = U32(int(str(key)))
            existing_bytes = memory.value
            padded_bytes = existing_bytes[:PAGE_SIZE] + [Byte(0x00)] * (PAGE_SIZE - len(existing_bytes))
            new_memory = Memory(
                access=Access(
                    inaccessible=Boolean(memory.access.inaccessible.value),
                    writable=Boolean(memory.access.writable.value),
                    readable=Boolean(True)
                ),
                value=Bytes(padded_bytes)
            )

            converted_pages[page_number] = new_memory

        return PageMemory(pages=Dictionary(converted_pages))

    @staticmethod
    def service_transition(test_service) -> AccountData:
        # Ensure the input is not None
        if test_service is None:
            return AccountData(
                storage=AccountStorage(),
                lookup=PreImageLookup(),
                timestamps=LookupTimestamps(),
                code_hash=ServiceCodeHash(ByteArray32([Byte(0x00)] * 32)),
                balance=Balance(U64(0)),
                gas_limit=Gas(U64(0)),
                min_gas=Gas(U64(0)),
            )

        # Extract and handle None values safely
        s_map = test_service.s_map or {}
        p_map = test_service.p_map or {}
        l_map = test_service.l_map or {}
        code_hash = test_service.code_hash or ByteVector32([Byte(0x00)] * 32)
        balance = test_service.balance or U64(0)
        gas_limit = test_service.g or U64(0)
        min_gas = test_service.m or U64(0)

        # Convert s_map and p_map to AccountStorage
        storage = AccountStorage()
        for key, value in s_map.items():
            storage[key] = value if value is not None else Bytes([])
        for key, value in p_map.items():
            storage[key] = value if value is not None else Bytes([])

        # Convert l_map to LookupTimestamps
        timestamps = LookupTimestamps()
        for key, value in l_map.items():
            lookup_table = LookupTable(hash=key, length=BlobLength(len(value.t) if value and value.t else 0))
            timestamps[lookup_table] = value.t if value and value.t else Timestamps([])

        return AccountData(
            storage=storage,
            lookup=PreImageLookup(),  # Assuming default behavior, modify if needed
            timestamps=timestamps,
            code_hash=ServiceCodeHash(code_hash),
            balance=Balance(balance),
            gas_limit=Gas(gas_limit),
            min_gas=Gas(min_gas),
        )

    @staticmethod
    def delta_transition(data) -> Delta:
        if data is None:
            return Delta()

        converted_data = {}
        for key, value in data.items():
            service_id = U32(int(str(key)))  # Convert string key to U32
            account_data = HostTransition.service_transition(value)  # Use existing function
            converted_data[service_id] = account_data

        return Delta(converted_data)

    @staticmethod
    def partial_state_transition(data):
        if data is None:
            return StateContext(delta=Delta({}), next_val_key=Iota([]), phi=Phi([]),
                                chi=Chi(chi_m=U32(0), chi_a=U32(0), chi_v=U32(0), chi_g=Dictionary({})))

        delta = HostTransition.delta_transition(data.D) if data.D is not None else Delta({})

        # Extract other fields safely
        next_val_key = data.I if data.I is not None else Iota([])
        phi = data.Q if data.Q is not None else Phi([])
        chi = data.X if data.X is not None else Chi(chi_m=U32(0), chi_a=U32(0), chi_v=U32(0),
                                                                      chi_g=Dictionary({}))
        return StateContext(delta, next_val_key, phi, chi)

    @staticmethod
    def xcontent_transition(test_xcontent):
        if test_xcontent is None:
            return XContent(
                s_index=ServiceId(0),  # Pass an explicit value, assuming it takes an integer
                partial_state=StateContext(
                    service_accounts=Delta({}),
                    validator_keys=0,
                    authorizer_keys=0,
                    privileges=0
                ),  # Check if this needs arguments
                i_index=ServiceId(0),
                deferred_transfers=DeferredTransfers(),  # Check if this needs arguments
                hash=ByteArray32([Byte(0) for _ in range(32)])
            )

        return XContent(
            s_index=test_xcontent.S if test_xcontent.S is not None else ServiceId.default(),
            partial_state=HostTransition.partial_state_transition(
                test_xcontent.U) if test_xcontent.U is not None else StateContext.default(),
            i_index=test_xcontent.I if test_xcontent.I is not None else ServiceId.default(),
            deferred_transfers=test_xcontent.T if test_xcontent.T is not None else DeferredTransfers.default(),
            hash=test_xcontent.Y if test_xcontent.Y is not None else ByteArray32.default()
        )

    @staticmethod
    def refine_map_transition(input_dict):
        refine_map = RefineMap()  # Always return a valid RefineMap

        if not input_dict:  # Handle None or empty dictionary
            return refine_map  # Return an empty RefineMap

        for key, value in input_dict.items():
            if not value:  # If value is None, create a default BoldM object
                blob = []
                memory = PageMemory(pages={})
                i = U64(0)
            else:
                blob = [byte.value for byte in getattr(value.P, "bytes", [])] if value.P else []
                memory = value.U if value.U else PageMemory(pages={})
                i = value.I if value.I else U64(0)

            refine_map[int(str(key))] = BoldM(blob=blob, memory=memory, i=i)

        return refine_map
