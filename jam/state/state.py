import os
import json
from copy import deepcopy
from typing import TYPE_CHECKING

from jam.error import JamError, JamErrorCode
from jam.state.partial import PartialState
from jam.utils.merkle import BMRFunctions
from jam.utils.task_utils import create_safe_task
from jam.state.accounts import DeltaView
from jam.state.storage import StateStorage, StateRecord
from jam.state.utils import make_state_prop
from tsrkit_types import Bytes, Dictionary
from jam.types import (
    Hash,
    Alpha,
    Eta,
    Omega,
    Pi,
    Psi,
    Kappa,
    Lambda_,
    Rho,
    Tau,
    Chi,
    Iota,
    Xi,
    Beta,
    Phi,
    Gamma,
    HeaderHash,
    OpaqueHash,
)
from jam.block.block import Block
from jam.types.state.theta import Theta
from jam.state.transitions import (
    Accumulation,
    Reporting,
    Authorization,
    RecentHistory,
    Safrole,
    Assurances,
    Disputes,
    Preimages,
    Statistics,
)
from jam.telemetry import emit_event
from jam.telemetry.events import (
    BestBlockChanged,
    Importing,
    BlockExecuted,
    BlockExecutionFailed,
    BlockOutline,
    ServiceExecution,
)
from tsrkit_types import U32, U64, Bytes32, String
from tsrkit_types.sequences import TypedVector
from dot_ring import Bandersnatch, IETF_VRF

from jam.utils.trie.merkle import StateTrie
if TYPE_CHECKING:
    from jam.settings import Settings
    from jam.finality.service import FinalityService
    from jam.jam_node import JamNode

class State:
    """
    State implementation that uses dynamic components fetched from Db
    Here we retain and update merkle trie as cache
    """

    # STF Lock, we can only process one Block at a time
    _lock = False
    # DB + Trie + Cache
    store: StateStorage

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
        return DeltaView(self.store, self._jam)

    @property
    def settings(self) -> "Settings":
        return self._jam.settings

    @property
    def trie(self) -> "StateTrie":
        return self.store._TRIE

    @property
    def publisher(self):
        return self._jam.responder.publisher

    @property
    def pool(self):
        return self._jam.pool

    @property
    def logger(self):
        return self._jam.logger

    @property
    def grandpa(self) -> "FinalityService":
        return self._jam.grandpa

    def __init__(self, jam: "JamNode", _store: StateStorage | None = None):
        if not _store:
            # TODO: Genesis must be default
            # Empty trie
            _trie = StateTrie()
            _store = StateStorage(_trie, jam.settings.state_db, {})

        self.store = _store
        self._jam = jam

    @classmethod
    def from_keyvals(cls, key_vals: dict[str, str] | dict[Bytes, Bytes], jam: "JamNode"):
        db = jam.settings.state_db

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

        return cls(jam, StateStorage(trie, db, {}))

    @property
    def root(self):
        # Use cached root if set (for snapshots loaded without trie mutations)
        # if hasattr(self, '_cached_root') and self._cached_root is not None:
        #     return self._cached_root
        return self.trie.root_hash

    def revert(self, header_hash):
        """
        Revert the node to a previous header_hash

        1. Collect all updates from latest -> header_hash
        2. Apply these to Trie + DB
        3. Clear cache
        """
        updates, _root = self.store.load_cache(header_hash, self._jam)
        self.store._updates = updates
        self.store.settle_cache()

    @classmethod
    def load(cls, jam: "JamNode", header_hash:HeaderHash | None = None) -> "State":
        """
        Load a snapshot of state at a particular block's slot.
        Create a cloned state (RO DB + cached updates)

        Args;
            - `header_hash`: Loads state at point in time when this header was imported.
            If this is not provided, we assume the request is just to have a readable instance of latest state
        """

        # Access finalized state
        state = jam.state
        
        # Create a clone of finalized state
        trie_snapshot = deepcopy(state.trie)
        store_snapshot = StateStorage(trie_snapshot, state.settings.state_db)

        state_snapshot = State(jam, store_snapshot)

        # Note: If Header Hash is not passed, cache remains empty
        cache, final_root = state_snapshot.store.load_cache(header_hash, jam, apply_trie=True)
        state_snapshot.store._updates = cache

        # Set the expected root directly from stored records
        state_snapshot._cached_root = final_root

        jam.logger.debug(
            "Loaded state instance.",
            header_hash=header_hash.hex(),
            state_root=state_snapshot.root.hex(),
        )

        return state_snapshot

    def stash(self, header_hash: HeaderHash):
        """Records all the cache updates in database."""
        self.store.record_cache(header_hash, self.settings.main_db, jam=self._jam)
        self.logger.debug(
            "State cache stashed.", header_hash=header_hash.hex(), state_root=self.root.hex()
        )

    def settle(self, header_hash: HeaderHash):
        """Settles a set of state changes and clears cache. Marks off the settlement with a unique header hash"""
        self.store.settle_cache()

        self._jam.state.store._TRIE = deepcopy(self.trie)
        self.logger.debug("State settled.", header_hash=header_hash.hex(), state_root=self._jam.state.root.hex())

    def _force_transition(self, block: Block, instant_finality: bool = True, skip_hooks: bool = False):
        """Force parent state transition wrapper.

        Loads the parent state and runs the block transition. If the parent
        state isn't ready yet (out-of-order block arrival), rejects early
        so the block can be re-received via a later announcement or sync.
        """
        parent_hash = block.header.parent

        # Guard: parent block must exist in DB
        if Block.load(parent_hash, self.settings.main_db) is None:
            self.logger.warning(
                "Parent block not in DB, skipping",
                parent=parent_hash.hex()[:16],
                slot=int(block.header.slot),
            )
            return False

        # Guard: parent must be fully processed (has StateRecord) or be the finalized block.
        # A block can exist in DB without a StateRecord when a concurrent async task
        # saved it via block.save() but hasn't finished stash/settle yet.
        finalized = self._jam.grandpa.load_final()
        if parent_hash != finalized.header.hash():
            state_key = StateStorage.get_storage_key(parent_hash)
            if self._jam.settings.main_db.get(state_key) is None:
                self.logger.warning(
                    "Parent state not settled yet, skipping",
                    parent=parent_hash.hex()[:16],
                    slot=int(block.header.slot),
                )
                return False

        parent_state = self.load(self._jam, parent_hash)
        parent_state.store.enable_cache()
        parent_state.store.enable_writes()
        return parent_state.transition(block, instant_finality, skip_hooks)

    def transition(self, block: Block, instant_finality: bool = True, skip_hooks=False) -> bool:
        """
        Main state transition function. Takes in the current state and the incoming block, returns the transitioned state

        Args:
            block: Incoming block
            instant_finality: Finality flag
            skip_hooks: Flag to bypass node activities
        """
        if self._lock:
            self.logger.error("Lock detected, skipping transition")
            return False

        self._lock = True

        event_id = id(block) & 0xFFFFFFFFFFFFFFFF
        try:
            header_hash = HeaderHash(block.header.hash())

            # Emit Importing event
            block_outline = BlockOutline(
                size=U32(len(block.encode())),
                header_hash=Bytes32(header_hash),
                num_tickets=U32(
                    len(block.extrinsic.tickets) if hasattr(block.extrinsic, "tickets") else 0
                ),
                num_preimages=U32(len(block.extrinsic.preimages)),
                preimages_size=U32(sum(len(p.encode()) for p in block.extrinsic.preimages)),
                num_guarantees=U32(len(block.extrinsic.guarantees)),
                num_assurances=U32(len(block.extrinsic.assurances)),
                num_disputes=U32(
                    len(block.extrinsic.disputes.verdicts)
                    + len(block.extrinsic.disputes.culprits)
                    + len(block.extrinsic.disputes.faults)
                ),
            )
            emit_event(Importing(slot=block.header.slot, block=block_outline))

            self.logger.debug(
                "Starting state transition on block",
                header_hash=header_hash.hex(),
                block_slot=int(block.header.slot),
                parent_hash=block.header.parent.hex()[:16] + "...",
                state_root=block.header.parent_state_root.hex()[:16] + "...",
                author_index=int(block.header.author_index),
                preimages=len(block.extrinsic.preimages),
                wrs=len(block.extrinsic.guarantees),
                assurances=len(block.extrinsic.assurances),
            )

            if block.header.slot == 0:
                self.logger.debug("Found genesis block, skipping", hh=header_hash.hex())
                self._lock = False
                return False

            if Block.load(header_hash, self.settings.main_db) is not None:
                self.logger.debug("Duplicate block found, skipping", hh=header_hash.hex())
                self._lock = False
                return False

            # Load pre state
            pre_state = self.load(self._jam, block.header.parent)


            # Disputes
            Disputes.transition(pre_state, self, block)


            # Safrole
            entropy_proof = IETF_VRF[Bandersnatch].from_bytes(block.header.entropy_source)
            vrf_output = OpaqueHash(entropy_proof.proof_to_hash(entropy_proof.output_point)[:32])
            Safrole.transition(pre_state, self, block, vrf_output)

            # Block Validation
            block_valid = block.validate(self, pre_state)

            # Handle Parent's Block Posterior State Root (β† h)
            # This must happen after validation (which checks previous root)
            # but before Reporting (which checks updated history)
            beta: Beta = self.beta
            if len(beta.h):
                beta.h[-1].state_root = block.header.parent_state_root
            self.beta = beta

            # Assurances
            _, newly_avail_wrs = Assurances.transition(pre_state, self, block)
            if len(newly_avail_wrs) > 0:
                self.logger.info(
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

            if block_valid:
                # Set local chain head to produced block
                # Save block in db, update ll create ghost block.
                block.save(self.settings.main_db)
                self.stash(header_hash)

                self.grandpa.set_head(block)

                self.logger.info(
                    "Block imported!",
                    hh=header_hash.hex()[:6],
                    t=int(self.tau),
                    sr=self.root.hex()[:6] + "..",
                )
                from jam.vectors import recorder as vec  # VECTOR
                if vec.is_active():  # VECTOR
                    vec.record_block(  # VECTOR
                        slot=self.tau, header_hash=header_hash,  # VECTOR
                        parent_hash=block.header.parent,  # VECTOR
                        pre_state_root=block.header.parent_state_root,  # VECTOR
                        post_state_root=self.root, author_index=block.header.author_index,  # VECTOR
                        block=block,  # VECTOR
                    )  # VECTOR
                    vec.record_state(self, header_hash)  # VECTOR
                emit_event(BestBlockChanged(slot=U32(int(self.tau)), hash=Bytes32(header_hash)))

                # Emit BlockExecuted event (services list is empty for now as we don't track individual service costs yet)
                emit_event(
                    BlockExecuted(
                        event_id=U64(event_id), services=TypedVector[ServiceExecution]([])
                    )
                )

                if not skip_hooks:
                    assurer = self._jam.operator.assurer

                    if assurer:
                        for ext in block.extrinsic.guarantees:
                            self.logger.debug(
                                "[ASSURER]: Fetching assigned shard", wr_hash=ext.report.hash().hex()
                            )
                            create_safe_task(assurer._req_shard(ext), "Request Shard")

                # TODO: Test Auditing & Refining with PJ
                # # Start Auditing for new block received
                # from jam.audit.audit_engine import AuditEngine
                # audit_engine = AuditEngine()
                # if len(newly_avail_wrs) > 0:
                #     asyncio.create_task(audit_engine.run(block=block, newly_avail_wrs=newly_avail_wrs))

                # TODO: Mark block as audited once audit process is done.
                # from jam.block.block_view import viewer
                # viewer.mark_as_audited(block, _set.main_db)
                # TODO: Remove Direct Finality
                # NOTE: We are setting instant finality here, this is to be updated once GRANDPA is implemented
                if instant_finality:
                    # Mark block as audited so best_block() follows the chain tip
                    self._jam.ledger.mark_as_audited(block)
                    # finalize the block and update viewer and whole chain
                    self.grandpa.finalise(block, True)
                    self.settle(header_hash)


                # Publishes updates of the statistics stored in chain state
                create_safe_task(
                    self.publisher.publish_statistics(self.pi),
                    name="Publish statistics"
                )

                self.pool.clear(block.extrinsic)

                self._lock = False
                return True
            else:
                raise JamError(JamErrorCode.INVALID_BLOCK)

        except JamError as jam_e:
            # Emit BlockExecutionFailed event
            emit_event(
                BlockExecutionFailed(event_id=U64(event_id), reason=String(str(jam_e)[:100]))
            )
            self.logger.error(
                "Invalid block",
                error=jam_e,
                hh=block.header.hash().hex(),
                slot=block.header.slot,
            )
            self.store.clear()
        self._lock = False

        return False

    def to_partial(self) -> "PartialState":
        return PartialState(
            self._jam,
            StateStorage(
                StateTrie(),
                self.store._DB,
                self.store._updates.copy(),
                cache_mode=True,
            )
        )

def setup_state(
    jam: "JamNode",
    genesis: str | dict | None = "dev-spec.json",
    replay: bool = False
) -> "State":
    state_db = jam.settings.state_db
    logger = jam.logger

    path = "dev-spec.json"

    if genesis == path and os.path.exists(path):
        source = "GenesisKV"
        genesis_json = json.load(open(genesis))
        data = Dictionary[Bytes, Bytes].from_json(genesis_json["genesis_state"])
    elif isinstance(genesis, dict):
        source = "KeyVals"
        data = genesis
    else:
        # NOTE: No need to replay state in this case
        source = "StateDB"
        data = state_db.get_all()

    logger.info(
        "Setting up state from genesis",
        genesis_type=type(genesis).__name__,
        genesis_source=source,
    )

    state = State.from_keyvals(data, jam)
    state.store.enable_writes()
    state.store.enable_cache()

    if source == "GenesisKV" or replay:
        # Replay state upto final block.
        final_blk = jam.grandpa.load_final()
        if final_blk and final_blk.header.slot > 0:
            replay_state(state, final_blk, jam)

    logger.info(
        "State setup completed",
        state_root=state.root.hex()[:16] + "...",
        data_entries=len(data),
    )

    return state

def replay_state(state: State, target_block: Block, jam: "JamNode") -> None:
    """Replay state updates from genesis to target block to restore Trie."""
    logger = jam.logger
    db = jam.settings.main_db

    logger.debug(f"Replaying state to block {target_block.header.slot}...")
    path = []
    curr = target_block
    while curr.header.slot > 0:
        path.append(curr)
        if curr.header.parent == bytes(32):
            break
        curr = Block.load(curr.header.parent, db)
        if not curr:
            logger.error(
                f"Broken chain at slot {path[-1].header.slot}, cannot replay state."
            )
            return

    path.reverse()

    count = 0
    for block in path:
        key = StateStorage.get_storage_key(block.header.hash())
        data = db.get(key)
        if data:
            record = StateRecord.decode(data)
            updates = {}
            deletes = []
            for k, u in record.updates.items():
                v = u.curr
                if v == bytes(0) or len(v) == 0:
                    deletes.append(k)
                else:
                    updates[k] = v

            if updates:
                state.trie.batch_update(updates)
            for k in deletes:
                state.trie.delete(k)
            count += 1
        else:
            logger.warning(f"Missing state record for block {block.header.slot}")

    logger.info(f"Replayed {count} blocks. Trie root: {state.trie.root_hash.hex()}")