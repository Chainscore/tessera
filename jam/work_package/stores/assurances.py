from rockstore import RockStore

from jam.types.work.report import WorkReport

from jam.work_package.store import DA

class AssurancesDA(DA):
    """
    Assurance DA Stores all the assurance

    Key: Core
    Value: Assurance (Header Hash (Anchor) + Bitfield + Ed25519 Signature)

    """
    def __init__(self, db : RockStore):
        self.prefix = bytes("AA", 'utf-8')
        self.db = db

    # TODO: Fix Assurance Type Later
    def put(self, report: WorkReport, assurance) -> None:
        key = self.prefix + report.core_index.encode()
        self.db.put(key, assurance.encode())

    def get(self, report : WorkReport):
        key =  self.prefix + report.core_index.encode()
        data = self.db.get(key)

        if data is None:
            raise KeyError("Assurance not found in DA")

    def __delete__(self, report : WorkReport) -> None:
        key = self.prefix + report.core_index.encode()
        self.db.delete(key)