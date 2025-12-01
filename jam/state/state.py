import json
import asyncio
from copy import copy, deepcopy

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
    HeaderHash, OpaqueHash,
)
from jam.block.block import Block
from jam.log_setup import block_logger as logger
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
from jam.api.rpc.subscription_handlers import subscribe_statistics

class State:
    """
    State implementation that uses dynamic components fetched from Db
    Here we retain and update merkle trie as cache
    """

    # STF Lock, we can only process only Block at a time
    _lock = False
    # DB + Trie + Cache
    store: StateStorage

    # State Components
    alpha       = make_state_prop(1,  Alpha)
    phi         = make_state_prop(2,  Phi)
    beta        = make_state_prop(3,  Beta)
    gamma       = make_state_prop(4,  Gamma)
    psi         = make_state_prop(5,  Psi)
    eta         = make_state_prop(6,  Eta)
    iota        = make_state_prop(7,  Iota)
    kappa       = make_state_prop(8,  Kappa)
    lambda_     = make_state_prop(9,  Lambda_)
    rho         = make_state_prop(10, Rho)
    tau         = make_state_prop(11, Tau)
    chi         = make_state_prop(12, Chi)
    pi          = make_state_prop(13, Pi)
    omega       = make_state_prop(14, Omega)
    xi          = make_state_prop(15, Xi)
    theta       = make_state_prop(16, Theta)

    @property
    def delta(self) -> "DeltaView":
        return DeltaView(self.store)

    def __init__(self, _store: StateStorage | None):
        self.store = _store

    @classmethod
    def from_keyvals(cls, key_vals: dict[str, str] | dict[Bytes, Bytes], db: RockStore):
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

        return cls(StateStorage(trie, db, {}))

    @property
    def root(self):
        return self.store._TRIE.root_hash

    def revert(self, header_hash):
        """
        Revert the node to a previous header_hash

        1. Collect all updates from latest -> header_hash
        2. Apply these to Trie + DB
        3. Clear cache
        """
        self.store._updates = self.store.load_cache(header_hash)
        self.store.settle_cache()

    @classmethod
    def load(cls, header_hash=HeaderHash(Hash.blake2b(b"empty"))) -> "State":
        """
        Load a snapshot of state at a particular block's slot.
        Create a cloned state (RO DB + Trie Clone w applied updates[do we really need trie?])

        Args;
            - `header_hash`: Loads state at point in time when this header was imported.
            If this is not provided, we assume the request is just to have a readable instance of latest state
        """
        # Create a clone of finalized state
        trie_snapshot = deepcopy(state.store._TRIE)
        store_snapshot = StateStorage(trie_snapshot, state.store._DB)

        state_snapshot = State(store_snapshot)

        # Load Past Updates
        # Note: If Header Hash is not passed, cache remains empty
        cache = state_snapshot.store.load_cache(header_hash)
        state_snapshot.store._updates = cache
        logger.debug("Loaded state instance.", header_hash=header_hash.hex(), state_root=state_snapshot.root.hex())

        return state_snapshot

    def stash(self, header_hash: HeaderHash):
        """Records all the cache updates in database."""
        from jam.settings import settings

        self.store.record_cache(header_hash, settings.main_db)
        logger.debug("State cache stashed.", header_hash=header_hash.hex(), state_root=self.root.hex())


    def settle(self, header_hash: HeaderHash):
        """Settles a set of state changes and clears cache. Marks off the settlement with an unique header hash"""
        self.store.settle_cache()

        # TEST: We are doing shallow copy here. Reference might stay same here.
        state.store._TRIE = self.store._TRIE
        logger.debug("State settled.", header_hash=header_hash.hex(), state_root=self.root.hex())


    @staticmethod
    def _force_transition(block: Block, instant_finality: bool = True):
        """Force parent state transition wrapper"""

        parent_state = state.load(block.header.parent)
        parent_state.store.enable_cache()
        parent_state.store.enable_writes()

        success = parent_state.transition(block, instant_finality)
        # del parent_state

        return success

    def transition(self, block: Block, instant_finality: bool = True) -> bool:
        """
        Main state transition function. Takes in the current state and the incoming block, returns the transitioned state

        Args:
            block: Incoming block
            instant_finality: Finality flag
        """

        if self._lock:
            logger.error("Lock detected, skipping transition")
            return False

        self._lock = True


        from jam.settings import settings as _set
        from jam.finality.finality import Finality

        try:
            header_hash = HeaderHash(block.header.hash())
            logger.debug(
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

            # TODO: Validate block headers
            # Epoch markers - make sure eta0_1 are the same as current etas
            # Tickets mark - make sure ticket.py are valid, present in gamma_a and outside in sequenced
            # Offenders mark - make sure offenders are present in psi.offenders

            if block.header.slot == 0:
                logger.debug("Found genesis block, skipping", hh=header_hash.hex())
                self._lock = False
                return False

            if _set.main_db.get(Block.get_storage_key_block(header_hash)) is not None:
                logger.debug("Duplicate block found, skipping", hh=header_hash.hex())
                self._lock = False
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
            vrf_output = Safrole.get_vrf_output(block.header.entropy_source)
            Safrole.transition(pre_state, self, block, vrf_output)

            # Assurances
            _, newly_avail_wrs = Assurances.transition(pre_state, self, block)
            if len(newly_avail_wrs) > 0:
                logger.info(
                    "Newly available WRs", count=len(newly_avail_wrs),
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
                TypedVector[Bytes](sorted([Bytes(comm[0].encode() + comm[1].encode()) for comm in self.theta])),
                Hash.keccak256
            )
            RecentHistory.transition(pre_state, self, block, accumulate_root, header_hash)

            # Preimages
            Preimages.transition(pre_state, self, block)

            # Statistics
            Statistics.transition(pre_state, self, block, newly_avail_wrs)

            if block.validate(self, pre_state):
                # Set local chain head to produced block
                # Save block in db, update ll create ghost block.
                block.save(_set.main_db)
                self.stash(header_hash)

                Finality.set_head(block, _set.main_db)

                logger.info(
                    "Block imported!",
                    new_wrs=newly_avail_wrs,
                    header=header_hash.hex()[:16] + "...",
                    timeslot=self.tau,
                    final_state_root=self.root.hex()[:16] + "...",
                )

                # TODO: Uncomment it for assurances
                # from jam.operations.handlers.assurer import assurer
                # for ext in block.extrinsic.guarantees:
                #     logger.debug("[ASSURER]: Fetching assigned shard", wr_hash=ext.report.hash().hex())
                #     asyncio.create_task(assurer._req_shard(ext))

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
                    # finalize the block and update viewer and whole chain
                    Finality.finalise(block, _set.main_db, True)
                    self.settle(header_hash)

                # Publishes updates of the statistics stored in chain state
                asyncio.create_task(subscribe_statistics(state.pi))

                block.extrinsic.clear_from_stores()

                self._lock = False
                return True
            else:
                raise JamError(JamErrorCode.INVALID_BLOCK)

        except JamError as jam_e:
            logger.error(
                "Invalid block", error=jam_e,
                hh=block.header.hash().hex(),
                slot=block.header.slot,
            )
            self.store.clear()
        self._lock = False

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


state = State(None)


def set_state(new_state: State):
    global state

    logger.info("Global state updated")

    state = new_state
    return state


def setup_state(state_db: RockStore, genesis: GhostState | str | dict = "dev-spec.json"):
    logger.info(
        "Setting up state from genesis",
        genesis_type=type(genesis).__name__,
        genesis_source=genesis if isinstance(genesis, str) else "GhostState",
    )

    if isinstance(genesis, str):
        genesis_json = json.load(open(genesis))
        data = Dictionary[Bytes, Bytes].from_json(genesis_json["genesis_state"])
    elif isinstance(genesis, GhostState):
        logger.debug("Transforming GhostState to genesis data")
        data = genesis.transform()
    else:
        data = genesis

    new_state = State.from_keyvals(data, state_db)
    new_state.store.enable_writes()
    new_state.store.enable_cache()

    logger.info(
        "State setup completed",
        state_root=new_state.root.hex()[:16] + "...",
        data_entries=len(data),
    )

    global state
    state = new_state

    # Init Executor
    from jam.state.transitions.safrole.executor import setup_executor
    try:
        pubkeys = [bytes(k.bandersnatch) for k in state.gamma.p]
        setup_executor(pubkeys)
    except Exception as e:
        logger.debug("Executor setup failed", err=str(e))

    return state
