from jam.incore.doer import Doer


class NodeDispatcher(Doer):
    """Base class for per-slot operator handlers. Subclass and override `run`."""

    async def run(self, time_slot: int):
        ...
