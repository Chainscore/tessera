from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jam.jam_node import JamNode

class Doer:
    def __init__(self, jam: "JamNode"):
        self.jam = jam

    @property
    def state(self):
        """Access Node State"""
        return self.jam.state

    @property
    def settings(self):
        """Access Node Settings"""
        return self.jam.settings

    @property
    def router(self):
        """Access Network Router"""
        return self.jam.router

    @property
    def responder(self):
        """Access RPC Responder"""
        return self.jam.responder

    @property
    def publisher(self):
        """Access RPC Subscription Publisher"""
        return self.jam.publisher

    @property
    def grandpa(self):
        """Access Finality Module"""
        return self.jam.grandpa

    @property
    def node(self):
        """Access Network Node"""
        return self.router.node

    @property
    def pool(self):
        """Access Extrinsic Pool"""
        return self.jam.pool

    @property
    def ledger(self):
        """Access State Ledger"""
        return self.jam.ledger

    @property
    def operator(self):
        """Access Node Operator Service"""
        return self.jam.operator

    @property
    def author(self):
        """Access Block Producer Module"""
        return self.jam.operator.author

    @property
    def assurer(self):
        """Access Report Assurer Module"""
        return self.jam.operator.assurer

    @property
    def conductor(self):
        """Access Ticket Conductor Module"""
        return self.jam.operator.conductor

    @property
    def postman(self):
        """Access Ticket Forwarding Module"""
        return self.jam.operator.postman

    @property
    def auditor(self):
        """Access Audit Engine Module"""
        return self.jam.auditor

    @property
    def logger(self):
        """Access Node Logger"""
        return self.jam.logger
