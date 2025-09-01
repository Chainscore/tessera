from typing import Any, Generic, List, TypeVar

from jam.block import DisputesExtrinsic
from jam.logging import get_logger


logger = get_logger("nodeops")

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
        if type(ext) == DisputesExtrinsic:
            self._validate(ext)
            self._store.append(ext)
        else:
            if ext in self._store:
                logger.debug(
                    "Duplicate extrinsic found",
                    ext=ext.__class__.__name__,
                    val=ext.to_json(),
                )
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
        for ext in ext_list:
            try:
                indx = self._store.index(ext)
                self._store.pop(indx)
            except ValueError as e:
                logger.debug(
                    "Extrinsic was not collected",
                    error=e,
                    ext=ext.__class__.__name__,
                    val=ext.to_json(),
                )

    def clear(self):
        self._store = []
