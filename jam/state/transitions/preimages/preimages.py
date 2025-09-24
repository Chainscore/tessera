import asyncio
import json

from jam.finality.finality import Finality
from jam.types import ServiceId
from jam.types.state.pi import ServiceStat
from copy import deepcopy
from tsrkit_types import Bytes
from jam.state.transitions.preimages.errors import PreimageError, PreimageErrorEnum
from jam.types.state.delta import LookupTable, Timestamps
from jam.types.state.sigma import Sigma
from jam.block import Block
from jam.block.extrinsics.preimages import Preimage, PreimagesExtrinsic
from jam.types.protocol.crypto import Hash
from jam.types.protocol.core import BlobLength


class Preimages:
    @staticmethod
    def transition(pre_state: Sigma, state: Sigma, block: Block) -> Sigma:
        """
        Transition the state with Preimages logic.

        Args:
            state: State before transition
            block: Block

        Returns:
            State after transition
        """
        Preimages.ensure_sorted_unique(block.extrinsic.preimages)

        # Go through each preimage in the block
        for preimage in block.extrinsic.preimages:
            # Find the account
            account = state.delta[preimage.requester]
            # If the preimage to add does not have lookup metadata, throw unneeded error
            hashed_blob = Hash.blake2b(preimage.blob)
            lookup_key = LookupTable(hash=hashed_blob, length=BlobLength(len(preimage.blob)))

            if account.lookup.get(lookup_key) is None or len(account.lookup.get(lookup_key)) != 0:
                raise PreimageError(
                    PreimageErrorEnum.PREIMAGE_UNNEEDED,
                    "Preimage metadata does not exist",
                )

        pi = state.pi
        for preimage in block.extrinsic.preimages:
            # Add the preimage to the account
            account = state.delta[preimage.requester]
            hashed_blob = Hash.blake2b(preimage.blob)
            lookup_key = LookupTable(Bytes[32](hashed_blob), BlobLength(len(preimage.blob)))

            account.preimages[hashed_blob] = preimage.blob
            metadata = account.lookup[lookup_key]
            metadata.append(block.header.slot)
            account.lookup[lookup_key] = metadata
            if preimage.requester not in pi.services:
                pi.services[preimage.requester] = ServiceStat.empty()
            curr_service_stat = pi.services[preimage.requester]
            curr_service_stat.provided_count += 1
            curr_service_stat.provided_size += len(preimage.blob)
        state.pi = pi

        from jam.settings import settings
        if settings.rpc_flag:
            from jam.api.rpc.broker import broker
            keys = broker.topics.keys()
            matches = [k for k in keys if "subscribeServiceRequest" in k]
            for req in matches:
                params = req.split(":")
                # ['subscribeServiceRequest', '0',
                #  '[190, 40, 209, 142, 179, 130, 108, 57, 75, 70, 177, 252, 4, 74, 224, 93, 191, 130, 151, 153, 194, 252, 49, 104, 23, 192, 93, 117, 207, 39, 52, 42]',
                #  '16296', 'True']

                hash_list = json.loads(params[2])

                # method = params[0]
                sid = ServiceId(params[1])
                pi_hash = bytes(hash_list)
                pi_len = BlobLength(params[3])
                finality = True if params[4] == 'True' else False

                account = state.delta[sid]
                lookup_key = LookupTable(Bytes[32](pi_hash), BlobLength(pi_len))
                value = account.lookup[lookup_key]

                last_publish = broker.last_publish

                if req not in last_publish or last_publish[req] != value:

                    from jam.settings import settings
                    block = Finality.load_final(settings.main_db) if finality else Finality.load_latest(settings.main_db)
                    asyncio.create_task(broker.publish(req,
                                                       {"header_hash": list(block.header.hash()),
                                                        "slot": int(block.header.slot), "value": value}))
                    broker.last_publish[req] = value

        return state

    @staticmethod
    def ensure_sorted_unique(preimages: PreimagesExtrinsic):
        """
        Checks if the extrinsic array is ordered and does not contain any duplicates

        Args:
            preimages: Preimages extrinsic

        Returns:
            True or False
        """

        def sort_fn(preimage: Preimage):
            # Take VRF output of the signature and sort by it
            return (
                int(preimage.requester),
                preimage.blob,
            )

        sorted_preimages = deepcopy(preimages)
        sorted_preimages.sort(key=sort_fn)

        # Check for duplicates in adjacent entries
        for i in range(1, len(sorted_preimages)):
            prev = sorted_preimages[i - 1]
            curr = sorted_preimages[i]
            if prev.requester == curr.requester and prev.blob == curr.blob:
                raise PreimageError(
                    PreimageErrorEnum.PREIMAGE_NOT_SORTED_UNIQUE,
                    "Duplicate preimage found",
                )

        if sorted_preimages != preimages:
            raise PreimageError(
                PreimageErrorEnum.PREIMAGE_NOT_SORTED_UNIQUE, "Preimages must be sorted"
            )
