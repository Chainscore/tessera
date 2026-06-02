from jam.models.state.pi import ServiceStat
from copy import deepcopy
from jam.state.transitions.preimages.errors import PreimageError, PreimageErrorEnum
from jam.models.state.delta import LookupTable, Timestamps
from jam.models.state.sigma import Sigma
from jam.block import Block
from jam.block.extrinsics.preimages import Preimage, PreimagesExtrinsic
from jam.models.protocol.crypto import Hash
from jam.models.protocol.core import BlobLength


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

        prepared_preimages = []
        for preimage in block.extrinsic.preimages:
            account = pre_state.delta[preimage.requester]
            hashed_blob = Hash.blake2b(preimage.blob)
            lookup_key = LookupTable(hash=hashed_blob, length=BlobLength(len(preimage.blob)))
            metadata = None if not account else account.lookup.get(lookup_key)

            if not account or metadata is None or len(metadata) != 0:
                raise PreimageError(
                    PreimageErrorEnum.PREIMAGE_UNNEEDED,
                    "Preimage metadata does not exist",
                )
            prepared_preimages.append((preimage, hashed_blob, lookup_key))

        pi = state.pi
        for preimage, hashed_blob, lookup_key in prepared_preimages:
            account = state.delta[preimage.requester]

            metadata = account.lookup.get(lookup_key)
            if metadata is not None:
                account.preimages[hashed_blob] = preimage.blob
                metadata.append(block.header.slot)
                account.lookup[lookup_key] = metadata
            if preimage.requester not in pi.services:
                pi.services[preimage.requester] = ServiceStat.empty()
            curr_service_stat = pi.services[preimage.requester]
            curr_service_stat.provided_count += 1
            curr_service_stat.provided_size += len(preimage.blob)
        state.pi = pi


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

        sorted_preimages = sorted( preimages, key=sort_fn)

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
