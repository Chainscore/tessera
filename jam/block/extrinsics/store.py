from typing import Generic, List, TypeVar

import structlog

T = TypeVar("T")


class ExtrinsicStore(Generic[T]):
    _store: List[T] = []

    def __init__(self) -> None:
        self._store = []
        self.logger = structlog.get_logger("node")

    @classmethod
    def _validate(cls, ext: T):
        if ext:
            return True
        return False

    def store(self, ext: T):
        from jam.block.extrinsics.disputes import DisputesExtrinsic

        if isinstance(ext, DisputesExtrinsic):
            if any(
                d.verdicts == ext.verdicts and
                d.culprits == ext.culprits and
                d.faults ==ext.faults
                for d in self._store
            ):
                self.logger.debug("Duplicate extrinsic found")
                return

        else:
            if ext in self._store:
                self.logger.debug(
                    "Duplicate extrinsic found",
                    ext=ext.__class__.__name__,
                    val=ext.to_json(),
                )
                return
            else:
                if not self._validate(ext):
                    self.logger.info(
                        "Invalid extrinsic found",
                        ext=ext.__class__.__name__,
                        val=ext.to_json(),
                    )
                else:
                    self._store.append(ext)

    def remove(self, ext_list: List[T]):
        """Remove the recently included extrinsics"""
        if not isinstance(ext_list, list):
            ext_list = [ext_list]
        else:
            ext_list = ext_list
        for ext in ext_list:
            try:
                indx = self._store.index(ext)
                self._store.pop(indx)
            except ValueError as e:
                self.logger.debug(
                    "Extrinsic was not collected",
                    ext=ext.__class__.__name__,
                    val=ext.to_json(),
                )

    def clear(self):
        self._store = []
