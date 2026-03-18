from rockstore import RockStore

from jam.types.work.package import WorkPackageHash, WorkPackage
from jam.storage.da.store import DA



class PackageDA(DA):
    """
    Package DA Stores all the packages received by a node

    Key: Work Package Hash
    Value: Work Package
    """

    def __init__(self, db: RockStore):
        self.prefix = bytes("WPACK", "utf-8")
        self.db = db

    def put(self, package: WorkPackage) -> None:
        key = self.prefix + package.hash().encode()
        self.db.put(key, package.encode())

    def get(self, wp_hash: WorkPackageHash) -> WorkPackage:
        key = self.prefix + wp_hash.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Package not found in DA")

        package, _ = WorkPackage.decode_from(data)

        return package

    def delete(self, wp_hash: WorkPackageHash) -> None:
        key = self.prefix + wp_hash.encode()
        self.db.delete(key)
