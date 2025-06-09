from tsrkit_types.enum import Enum

class Accessibility(Enum):
    NULL = "Non-Accessible"
    WRITE = "Writable"
    READ = "Readable"
