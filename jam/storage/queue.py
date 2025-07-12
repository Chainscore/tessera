from tsrkit_types.struct import structure
from rockstore import RockStore
from tsrkit_types.integers import Uint


@structure
class StorageQueueMetadata:
    """Metadata for the storage queue."""

    head: Uint  # index of the head of the queue, first item to be popped
    tail: Uint  # index of the tail of the queue, next item to be pushed
    count: Uint  # number of items in the queue


class StorageQueue:
    """
    Storeage queue for storing and fetching sequencial data from KV store.
    """

    queue_name: str

    def __init__(self, queue_name: str):
        self.queue_name = queue_name

    @property
    def meta_key(self) -> bytes:
        """Key for the metadata of the storage queue."""
        return f"{self.queue_name}:metadata".encode()

    def item_key(self, index: int) -> bytes:
        """Key for the item in the queue."""
        return f"{self.queue_name}:{index}".encode()

    def metadata(self, db: RockStore) -> StorageQueueMetadata:
        """Get the metadata of the storage queue."""
        metadata = db.get(self.meta_key)
        if metadata is None:
            return StorageQueueMetadata(head=Uint(0), tail=Uint(0), count=Uint(0))
        return StorageQueueMetadata.decode(metadata)

    def push(self, db: RockStore, value: bytes) -> int:
        """Push an item to the queue."""
        metadata = self.metadata(db)
        db.put(self.item_key(int(metadata.tail)), value)
        metadata.tail = Uint(int(metadata.tail) + 1)
        metadata.count = Uint(int(metadata.count) + 1)
        db.put(self.meta_key, metadata.encode())
        return int(metadata.tail)

    def key_of(self, db: RockStore, value: bytes) -> int:
        """Get the index of an item in the queue."""
        metadata = self.metadata(db)
        for i in range(int(metadata.head), int(metadata.tail)):
            key = self.item_key(i)
            if db.get(key) == value:
                return key
        return None

    def remove_key(self, db: RockStore, key: bytes):
        """Remove an item from the queue by key."""
        metadata = self.metadata(db)
        db.delete(key)
        metadata.count -= 1
        db.put(self.meta_key, metadata.encode())

    def remove_value(self, db: RockStore, value: bytes):
        """Remove an item from the queue by value."""
        key = self.key_of(db, value)
        if key:
            self.remove_key(db, key)

    def get(self, db: RockStore, count: int = 1, skip: int = 0) -> list[bytes]:
        """Get items from the queue, starting from the head.

        Args:
            queue_name (str): identifier name of the queue
            db (RockStore): database
            count (int, optional): number of items to get. Defaults to 1.
            skip (int, optional): number of items to skip. Defaults to 0.

        Returns:
            list[bytes]: list of items from the queue
        """
        metadata = self.metadata(db)
        items = []

        # pre checks
        if skip >= int(metadata.count) or count == 0 or metadata.head == metadata.tail:
            return items

        if count == -1:
            count = int(metadata.count) - skip

        # get items, skipping the first skip items
        # and appending the next count items to the list
        for i in range(int(metadata.head), int(metadata.tail)):
            key = self.item_key(i)
            value = db.get(key)
            if value:
                skip -= 1
                if skip < 0:
                    items.append(value)
                    count -= 1
            if count == 0:
                break

        return items

    def pop(self, db: RockStore) -> bytes | None:
        """
        Pop an item from the queue. Returns None if the queue is empty.

        TODO - Handle duplicates
        """
        metadata = self.metadata(db)
        value = db.get(self.item_key(int(metadata.head)))

        # iterate and push head pointer until a value is found
        while value is None:
            metadata.head += 1
            value = db.get(self.item_key(int(metadata.head)))
            if metadata.head >= metadata.tail:
                return None
        # delete the item
        db.delete(self.item_key(int(metadata.head)))

        # update metadata
        metadata.head += 1
        metadata.count -= 1
        db.put(self.meta_key, metadata.encode())
        return value
