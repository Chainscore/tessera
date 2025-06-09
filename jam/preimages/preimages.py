from copy import deepcopy

from jam.preimages.errors import PreimageError, PreimageErrorEnum
from jam.types.state.delta import LookupTable
from jam.types.state.sigma import Sigma
from jam.types.block import Block
from jam.types.block.extrinsics.preimages import Preimage, PreimagesExtrinsic
from jam.types.protocol.crypto import Hash
from jam.types.protocol.core import BlobLength
from jam.types.state.pi import ServiceStat


class Preimages:
    @staticmethod
    def transition(state: Sigma, block: Block) -> Sigma:
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
            lookup_key = LookupTable(hashed_blob, BlobLength(len(preimage.blob)))
            if (
                lookup_key not in account.lookup
                or len(account.lookup[lookup_key]) != 0
            ):
                raise PreimageError(
                    PreimageErrorEnum.PREIMAGE_UNNEEDED,
                    "Preimage metadata does not exist",
                )

        for preimage in block.extrinsic.preimages:
            # Add the preimage to the account
            account = state.delta[preimage.requester]
            hashed_blob = Hash.blake2b(preimage.blob)
            lookup_key = LookupTable(hashed_blob, BlobLength(len(preimage.blob)))

            account.preimages[hashed_blob] = preimage.blob
            account.lookup[lookup_key].append(block.header.slot)
            if preimage.blob is not None:
                if preimage.requester not in state.pi.services:
                    state.pi.services[preimage.requester] = ServiceStat.empty()
                curr_service_stat = state.pi.services[preimage.requester]
                curr_service_stat.provided_count += 1
                curr_service_stat.provided_size += len(preimage.blob)
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
                str(preimage.blob),
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
