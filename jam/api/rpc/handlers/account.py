"""
Service Handler

Handlers for service-related RPC methods.
"""
from jam.block.extrinsics.preimages import Preimage
from jam.state.state import State
from jam.types.state.delta import LookupTable, AccountMetadata, Timestamps
from jam.types.protocol.crypto import HeaderHash, OpaqueHash
from jam.types.protocol.core import ServiceId, BlobLength
from jam.api.rpc.handlers.base import BaseHandler
from jam.api.rpc.utils.serialization import parse_params
from tsrkit_types import Bytes


class ServiceHandler(BaseHandler):
    """Handler for service-related RPC methods."""

    def service_data(self, params: list) -> AccountMetadata | None:
        """Returns the storage data for the service with the given ID."""
        header_hash, service_id = parse_params([HeaderHash, ServiceId], params)
        state = State.load(self.jam, header_hash)
        account = state.delta.get(service_id)

        if not account:
            return None

        service = account.service

        meta = AccountMetadata(
            code_hash=service.code_hash,
            balance=service.balance,
            gas_limit=service.gas_limit,
            min_gas=service.min_gas,
            num_i=service.num_i,
            num_o=service.num_o,
            gratis_offset=service.gratis_offset,
            created_at=service.created_at,
            accumulated_at=service.accumulated_at,
            parent_service=service.parent_service,
        )

        return meta

    def service_value(self, params: list) -> Bytes | bytes | None:
        """Returns the value associated with the given service ID and key."""
        header_hash, service_id, key = parse_params([HeaderHash, ServiceId, Bytes], params)
        state = State.load(self.jam, header_hash)
        return state.delta[service_id].storage.get(key)

    def service_preimage(self, params: list) -> Bytes | bytes:
        """Returns the preimage of the given hash."""
        header_hash, service_id, hash_val = parse_params(
            [HeaderHash, ServiceId, OpaqueHash], params
        )
        state = State.load(self.jam, header_hash)
        blob = state.delta[service_id].preimages.get(hash_val)
        return blob if blob else None

    def service_request(self, params: list) -> Timestamps | None:
        """Returns the preimage request associated with the given service ID and hash/length."""
        header_hash, service_id, hash_val, length = parse_params(
            [HeaderHash, ServiceId, OpaqueHash, BlobLength], params
        )
        state = State.load(self.jam, header_hash)
        lookup_key = LookupTable(hash_val, length)
        return state.delta[service_id].lookup.get(lookup_key)

    def list_services(self, params: list) -> list[int]:
        """Returns a list of all services currently known to be on JAM."""
        (header_hash,) = parse_params([HeaderHash], params)
        state = State.load(self.jam, header_hash)
        return [int(sid) for sid in state.delta.keys()]

    async def submit_preimage(self, params: list) -> None:
        """Submit a preimage which is being requested by the given service."""
        s_id, preimage = parse_params([ServiceId, Bytes], params)

        pre_img = Preimage(requester=s_id, blob=Bytes(preimage))
        self.pool.preimages.store(pre_img, jam=self.jam)

        return None
