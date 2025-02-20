from jam.preimages.errors import PreimageError, PreimageErrorEnum
from jam.state.components.delta import LookupTable
from jam.state.state import State
from jam.types.block import Block
from jam.types.extrinsics.preimages import PreimagesExtrinsic, Preimage
from jam.types.protocol.crypto import Hash


class Preimages:
    @staticmethod
    def transition(pre_state: State, block: Block) -> State:
        Preimages.ensure_sorted(block.extrinsic.preimages)

        # Go through each preimage in the block
        for preimage in block.extrinsic.preimages:
            # Find the account
            account = pre_state.delta[preimage.requester]
            # Add the preimage to the account
            # If the preimage to add does not have lookup metadata, throw unneeded error
            lookup_key = LookupTable(Hash.sha256(preimage.blob), len(preimage.blob))
            if lookup_key not in account.timestamps:
                raise PreimageError(PreimageErrorEnum.PREIMAGE_UNNEEDED, "Preimage metadata does not exist")
        return pre_state

    @staticmethod
    def ensure_sorted(preimages: PreimagesExtrinsic):
        def sort_fn(preimage: Preimage):
            # Take VRF output of the signature and sort by it
            return (int(preimage.requester), int.from_bytes(bytes(preimage.blob), 'little'))
        sorted_preimages = preimages.copy()
        sorted_preimages.sort(key=sort_fn)
        print([sort_fn(pr) for pr in sorted_preimages])
        if sorted_preimages != preimages:
            raise PreimageError(PreimageErrorEnum.PREIMAGE_NOT_SORTED_UNIQUE, "Preimages must be sorted")