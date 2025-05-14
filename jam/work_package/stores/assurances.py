from jam.db.kv import KVStore
from jam.types import Int
from jam.work_package.store import DA
from jam.types.extrinsics.assurances import Assurance
from jam.types.work.report import WorkReport
from jam.types.block import Block

class AssurancesDA(DA):
    """
    Assurance DA Stores all the assurance

    Key: Core
    Value: Assurance (Header Hash (Anchor) + Bitfield + Ed25519 Signature)

    """

    def __init__(self, db : KVStore):
        self.prefix = bytes("AA", 'utf-8')
        self.db = db

    def put(self, report: WorkReport, assurance : Assurance) -> None:
        key = self.prefix + report.core_index.encode()
        self.db.put(key, assurance.encode())

    def get(self, report : WorkReport) -> Assurance:
        key =  self.prefix + report.core_index.encode()
        data = self.db.get(key)

        if data is None:
            raise KeyError("Assurance not found in DA")

    def __delete__(self, report : WorkReport) -> None:
        key = self.prefix + report.core_index.encode()
        self.db.delete(key)