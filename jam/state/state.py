import json
import asyncio
from copy import copy, deepcopy
from typing import Optional

from jam.error import JamError, JamErrorCode
from jam.state.partial import PartialState
from jam.utils.merkle import BMRFunctions
from rockstore import RockStore
from jam.state.accounts import DeltaView
from jam.state.ghost import GhostState
from jam.utils.trie.merkle import StateTrie
from jam.state.storage import StateStorage
from jam.state.utils import make_state_prop
from tsrkit_types import Bytes, Dictionary, TypedVector
from jam.types import (
    Hash, Alpha, Eta, Omega, Pi, Psi, Kappa, Lambda_, Rho, Tau, Chi, Iota, Xi, Beta, Phi, Gamma,
    HeaderHash, OpaqueHash
)
from jam.block.block import Block
from jam.log_setup import block_logger as logger
from jam.types.state.theta import Theta, Commitment
from jam.state.transitions import (
    Accumulation, Reporting, Authorization, RecentHistory, Safrole, Assurances, Disputes, Preimages, Statistics
)

# Global state instance (initialized by JamNode)
state: Optional["State"] = None
from jam.api.rpc.subscription_handlers import subscribe_statistics
from jam.telemetry import emit_event
from jam.telemetry.events import (
    BestBlockChanged, Importing, BlockExecuted, BlockExecutionFailed, BlockOutline, ServiceExecution
)
from tsrkit_types import U32, U64, Bytes32, String
from tsrkit_types.sequences import TypedVector
from dot_ring import RingVRF, Bandersnatch, IETF_VRF

# Forward declaration to avoid circular import issues if possible, 
# but python handles this freely usually.
# from jam.finality.service import FinalityService 

class State:
    """
    State implementation that uses dynamic components fetched from Db
    Here we retain and update merkle trie as cache
    """

    # DB + Trie + Cache
    store: StateStorage
    
    # Dependencies
    finality_service: Optional["FinalityService"] = None

    # State Components
    alpha = make_state_prop(1, Alpha)
    phi = make_state_prop(2, Phi)
    beta = make_state_prop(3, Beta)
    gamma = make_state_prop(4, Gamma)
    psi = make_state_prop(5, Psi)
    eta = make_state_prop(6, Eta)
    iota = make_state_prop(7, Iota)
    kappa = make_state_prop(8, Kappa)
    lambda_ = make_state_prop(9, Lambda_)
    rho = make_state_prop(10, Rho)
    tau = make_state_prop(11, Tau)
    chi = make_state_prop(12, Chi)
    pi = make_state_prop(13, Pi)
    omega = make_state_prop(14, Omega)
    xi = make_state_prop(15, Xi)
    theta = make_state_prop(16, Theta)

    @property
    def delta(self) -> "DeltaView":
        return DeltaView(self.store)

    def __init__(self, _store: StateStorage | None, finality_service: Optional["FinalityService"] = None, settings = None):
        self.store = _store
        self.finality_service = finality_service
        self.settings = settings
        self._transition_lock = False

    @classmethod
    def from_keyvals(cls, key_vals: dict[str, str] | dict[Bytes, Bytes], db: RockStore, finality_service: Optional["FinalityService"] = None, settings = None):
        state_dict: dict[Bytes, Bytes] = {}
        if len(key_vals) > 0 and isinstance(list(key_vals.keys())[0], str):
            for k, v in key_vals.items():
                state_dict[Bytes.fromhex(k)] = Bytes.fromhex(v)
        else:
            state_dict = key_vals

        trie = StateTrie()
        trie.merkelize(state_dict)

        for k, v in state_dict.items():
            db.put(k, v)

        return cls(StateStorage(trie, db, {}), finality_service, settings)

    @property
    def root(self):
        # Use cached root if set (for snapshots loaded without trie mutations)
        if hasattr(self, "_cached_root") and self._cached_root is not None:
            return self._cached_root
        return self.store._TRIE.root_hash

    def revert(self, header_hash):
        """
        Revert the node to a previous header_hash
        """
        updates, _root = self.store.load_cache(header_hash)
        self.store._updates = updates
        self.store.settle_cache()

    def load(self, header_hash=HeaderHash(Hash.blake2b(b"empty"))) -> "State":
        """
        Load a snapshot of state at a particular block's slot.
        """
        # Create a clone of finalized state logic
        # We need access to the current state's components to clone deeply
        # Assuming `self` is currently the best/finalized state reference
        
        trie_snapshot = deepcopy(self.store._TRIE)
        store_snapshot = StateStorage(trie_snapshot, self.store._DB)

        state_snapshot = State(store_snapshot, self.finality_service, self.settings)

        # Note: If Header Hash is not passed, cache remains empty
        cache, final_root = state_snapshot.store.load_cache(header_hash, apply_trie=True)
        state_snapshot.store._updates = cache

        # Set the expected root directly from stored records
        state_snapshot._cached_root = final_root

        logger.debug(
            "Loaded state instance.",
            header_hash=header_hash.hex(),
            state_root=state_snapshot.root.hex(),
        )

        return state_snapshot

    def stash(self, header_hash: HeaderHash):
        """Records all the cache updates in database."""
        # TODO: removing settings dependency?
        # Ideally DB is passed into State or accessed via self.store._DB
        # record_cache uses self.store._DB which is good.
        # But legacy `settings.main_db` was passed. 
        # `StateStorage.record_cache` signature: def record_cache(self, header_hash, db: RockStore):
        # We can use self.store._DB? No, StateStorage has _DB (State DB), main_db is Block DB usually.
        # We might need to inject main_db too or access it via finality service/store.
        
        # For now, assume store._DB is the unified DB or we need access to main DB
        # Re-using the passed DB in init/load which seems to be the intended DB.
        
        # If State DB and Block DB are separate, we have a problem.
        # Looking at jam/settings.py, they are usually separate (state_db vs main_db).
        
        # NOTE: WE NEED MAIN DB HERE.
        # Let's use finality_service.db if available, as that wraps main_db usually.
        if self.finality_service:
            self.store.record_cache(header_hash, self.finality_service.db)
        else:
            logger.warning("No finality service or main DB available to stash cache")

        logger.debug(
            "State cache stashed.", header_hash=header_hash.hex(), state_root=self.root.hex()
        )

    def settle(self, header_hash: HeaderHash):
        """Settles a set of state changes and clears cache. Marks off the settlement with an unique header hash"""
        self.store.settle_cache()

        # Update the TRIE reference for this instance (shallow copy logic from original)
        # self.store._TRIE = self.store._TRIE # redundant?
        logger.debug("State settled.", header_hash=header_hash.hex(), state_root=self.root.hex())

    def _force_transition(self, block: Block, instant_finality: bool = True):
        """Force parent state transition wrapper"""

        parent_state = self.load(block.header.parent)
        parent_state.store.enable_cache()
        parent_state.store.enable_writes()

        success = parent_state.transition(block, instant_finality)
        return success

    def transition(self, block: Block, instant_finality: bool = True, skip_hooks=False) -> bool:
        """
        Main state transition function.
        """

        if self._transition_lock:
            logger.error("Lock detected, skipping transition")
            return False

        self._transition_lock = True

        try:
            header_hash = HeaderHash(block.header.hash())
            event_id = id(block) & 0xFFFFFFFFFFFFFFFF

            # Emit Importing event
            block_outline = BlockOutline(
                size=U32(len(block.encode())),
                header_hash=Bytes32(header_hash),
                num_tickets=U32(len(block.extrinsic.tickets) if hasattr(block.extrinsic, "tickets") else 0),
                num_preimages=U32(len(block.extrinsic.preimages)),
                preimages_size=U32(sum(len(p.encode()) for p in block.extrinsic.preimages)),
                num_guarantees=U32(len(block.extrinsic.guarantees)),
                num_assurances=U32(len(block.extrinsic.assurances)),
                num_disputes=U32(len(block.extrinsic.disputes.verdicts) + len(block.extrinsic.disputes.culprits) + len(block.extrinsic.disputes.faults)),
            )
            emit_event(Importing(slot=block.header.slot, block=block_outline))

            if block.header.slot == 0:
                logger.debug("Found genesis block, skipping", hh=header_hash.hex())
                self._transition_lock = False
                return False

            if self.finality_service and self.finality_service.db.get(Block.get_storage_key_block(header_hash)) is not None:
                logger.debug("Duplicate block found, skipping", hh=header_hash.hex())
                self._transition_lock = False
                return False

            # Load pre state
            pre_state = self.load(block.header.parent)

            # Handle Parent's Block Posterior State Root (β† h)
            beta: Beta = self.beta
            if len(beta.h):
                beta.h[-1].state_root = block.header.parent_state_root
            self.beta = beta

            # Disputes
            Disputes.transition(pre_state, self, block)

            # Safrole
            entropy_proof = IETF_VRF[Bandersnatch].from_bytes(block.header.entropy_source)
            vrf_output = OpaqueHash(entropy_proof.proof_to_hash(entropy_proof.output_point)[:32])
            Safrole.transition(pre_state, self, block, vrf_output)

            # Block Validation - needs self context
            if not block.validate(self, pre_state, self.settings):
                 raise JamError(JamErrorCode.INVALID_BLOCK)

            # Assurances
            _, newly_avail_wrs = Assurances.transition(pre_state, self, block)
            if len(newly_avail_wrs) > 0:
                logger.info(
                    "Newly available WRs",
                    count=len(newly_avail_wrs),
                    wrs=[wr.hash().hex()[:16] + "..." for wr in newly_avail_wrs],
                )

            # Reporting
            Reporting.transition(pre_state, self, block, [])

            # Accumulation
            _, commitment_map = Accumulation.transition(
                pre_state, self, block, newly_avail_wrs=newly_avail_wrs
            )

            # Authorization
            Authorization.transition(pre_state, self, block)

            # Recent History
            bmr_merklizer = BMRFunctions()

            # Calculate Merkle root of Accumulation Outputs
            accumulate_root = bmr_merklizer.wb_merklize(
                TypedVector[Bytes](
                    [Bytes(comm.service_id.encode() + comm.output.encode()) for comm in self.theta]
                ),
                Hash.keccak256,
            )
            RecentHistory.transition(pre_state, self, block, accumulate_root, header_hash)

            # Preimages
            Preimages.transition(pre_state, self, block)

            # Statistics
            Statistics.transition(pre_state, self, block, newly_avail_wrs)

            # --- Success ---
            # Set local chain head to produced block
            # Save block in db, update ll create ghost block.
            if self.finality_service:
                block.save(self.finality_service.db)
                self.stash(header_hash)
                
                self.finality_service.set_head(block)

                logger.info(
                    "Block imported!",
                    hh=header_hash.hex()[:6],
                    t=int(self.tau),
                    sr=self.root.hex()[:6] + "..",
                )
                emit_event(BestBlockChanged(slot=U32(int(self.tau)), hash=Bytes32(header_hash)))

                # Emit BlockExecuted event
                emit_event(
                    BlockExecuted(
                        event_id=U64(event_id), services=TypedVector[ServiceExecution]([])
                    )
                )

                if not skip_hooks:
                    from jam.operations.handlers.assurer import assurer

                    for ext in block.extrinsic.guarantees:
                        logger.debug(
                            "[ASSURER]: Fetching assigned shard", wr_hash=ext.report.hash().hex()
                        )
                        asyncio.create_task(assurer._req_shard(ext))

                if instant_finality:
                    try:
                        self.finality_service.finalise(block, initial=True)
                        self.settle(header_hash)
                    except ValueError as e:
                        logger.warning("Failed to finalize block (fork?)", error=e, hh=header_hash.hex()[:8])
                        self._transition_lock = False
                        return False

                # Publishes updates of the statistics stored in chain state
                asyncio.create_task(subscribe_statistics(self.pi))

            block.extrinsic.clear_from_stores()

            self._transition_lock = False
            return True

        except JamError as jam_e:
            emit_event(
                BlockExecutionFailed(event_id=U64(event_id), reason=String(str(jam_e)[:100]))
            )
            logger.error(
                "Invalid block",
                error=jam_e,
                hh=block.header.hash().hex(),
                slot=block.header.slot,
            )
            # Rollback/Clear cache
            self.store.clear()
        
        self._transition_lock = False
        return False

    def to_partial(self) -> "PartialState":
        return PartialState(
            StateStorage(
                StateTrie(),
                self.store._DB,
                self.store._updates.copy(),
                cache_mode=True,
            )
        )
