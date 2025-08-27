class NodeDispatcher:
    """
    Interface defining how a dispatch function should be.

    Overwrite the run fn, please them in ./handlers

    """

    @classmethod
    async def run(cls, time_slot: int):
        ...
