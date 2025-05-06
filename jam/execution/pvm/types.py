from jam.types.base.enum import Enum

class Accessibility(Enum):
    null:"Non-Accessible"
    write:"Writable"
    read:"Readable"

class Status(Enum):
    PANIC = "panic"
    HALT = "halt"
    PAGE_FAULT = "page-fault"
    HOST = "host-call"
    OUT_OF_GAS = "out-of-gas"
    CONTINUE = "continue"

    def with_number(self, num):
        return self.value, num
