from typing import Any, Generic, List, TypeVar
from jam.log_setup import node_logger as logger

T = TypeVar("T")


class ExtrinsicStore(Generic[T]):
    _store: List[T] = []

    def __init__(self) -> None:
        self._store = []

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
                logger.debug("Duplicate extrinsic found")
                return

        else:
            if ext in self._store:
                logger.debug(
                    "Duplicate extrinsic found",
                    ext=ext.__class__.__name__,
                    val=ext.to_json(),
                )
                return
            else:
                if not self._validate(ext):
                    logger.info(
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
                logger.debug(
                    "Extrinsic was not collected",
                    ext=ext.__class__.__name__,
                    val=ext.to_json(),
                )

    def clear(self):
        self._store = []
