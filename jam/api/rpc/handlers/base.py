"""
Base Handler

Base class for all RPC handlers with access to JamNode.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jam.jam_node import JamNode


class BaseHandler:
    """
    Base class for all RPC handlers.

    Provides:
    - Access to JamNode (state, settings, etc.)
    - Common helper methods
    """

    def __init__(self, jam_node: "JamNode"):
        self._jam = jam_node

    @property
    def jam(self):
        """Access to JamNode."""
        return self._jam

    @property
    def router(self):
        """Access to Networking Service."""
        return self._jam.router

    @property
    def settings(self):
        """Access to node settings."""
        return self._jam.settings

    @property
    def state(self):
        """Access to chain state."""
        return self._jam.state

    @property
    def grandpa(self):
        """Access to finality module."""
        return self._jam.grandpa

    @property
    def pool(self):
        """Access to extrinsic pool."""
        return self._jam.pool

    @property
    def main_db(self):
        """Access to main database."""
        return self._jam.settings.main_db
