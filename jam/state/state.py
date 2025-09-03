import json
from typing import Type
from jam.error import JamError, JamErrorCode
from jam.state.partial import PartialState
from jam.utils.merkle import BMRFunctions
from rockstore import RockStore
from jam.state.accounts import DeltaView
from jam.state.ghost import GhostState
from jam.utils.trie.merkle import StateTrie
from jam.state.storage import StateStorage
from jam.state.utils import construct_state_key, make_state_prop
from tsrkit_types import Bytes, Codable, Dictionary, TypedVector
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
)
from jam.block.block import Block
from jam.logging import get_logger
from jam.types.state.theta import Theta

logger = get_logger("import")


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
        self.store._updates = self.store._load_updates(header_hash)
        self.store.save_n_clear_cache()

    @classmethod
    def load(cls, header_hash=HeaderHash(Hash.blake2b(b"empty"))) -> "State":
        """
        Load a readable instance of state. Made for serving API data.
        Create a cloned state (RO DB + Trie Clone w applied updates[do we really need trie?])

        Args;
            - `header_hash`: Loads state at point in time when this header was imported.
            If this is not provided, we assume the request is just to have a readable instance of latest state
        """
        from jam.settings import settings

        # Empty trie -I dont think we need past trie data anywhere
        trie = StateTrie()
        # Create a Read-Only instance
        db = RockStore(state.store._DB.path.decode(), options={"read_only": True})
        # Load past updates
        cache = state.store._load_updates(header_hash)

        return State(StateStorage(trie, db, cache))

    def settle(self, header_hash: HeaderHash):
        """Settles a set of state changes cached in store. Marks off the settlement with an unique header hash"""
        from jam.settings import settings

        self.store.save_n_clear_cache(header_hash, settings.main_db)

    def _force_transition(self, block: Block):
        # 1. Push auth hash of every WR to self.alpha[0:1]

        # TODO: We should remove this
        # Comment these lines to turn off force transition
        logger.warning("Force State Transition: ON")
        alpha = self.alpha

        for guarantee in block.extrinsic.guarantees:
            report = guarantee.report
            alpha[report.core_index][0] = report.authorizer_hash

        self.alpha = alpha

        return self.transition(block)

    def transition(self, block: Block) -> bool:
        """
        Main state transition function. Takes in the current state and the incoming block, returns the transitioned state

        Args:
            block: Incoming block
        """
        if self._lock:
            logger.error("Lock detected, skipping transition")
            return False

        self._lock = True

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

            pre_state = self.load()

            # Handle Parent's Block Posterior State Root (β† h)
            beta: Beta = self.beta
            if len(beta.h):
                beta.h[-1].state_root = block.header.parent_state_root
            self.beta = beta

            # Disputes
            Disputes.transition(pre_state, self, block)

            # TODO: Ensure correct ordering of module transitions
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
                TypedVector[Bytes](sorted([Bytes(comm[0].encode() + comm[1].encode()) for comm in state.theta])),
                Hash.keccak256
            )
            RecentHistory.transition(pre_state, self, block, accumulate_root, header_hash)

            # Preimages
            Preimages.transition(pre_state, self, block)

            # Statistics
            Statistics.transition(pre_state, self, block, newly_avail_wrs)

            if True: #block.validate():
                state.settle(header_hash)

                # Set local chain head to produced block
                block.save(_set.main_db)
                Finality.set_head(header_hash, _set.main_db)
                logger.info(
                    "Block imported!",
                    new_wrs=newly_avail_wrs,
                    header=header_hash.hex()[:16] + "...",
                    timeslot=self.tau,
                    final_state_root=self.root.hex()[:16] + "...",
                )


                # from jam.operations.handlers.assurer import assurer
                # for ext in block.extrinsic.guarantees:
                #     logger.debug("[ASSURER]: Fetching assigned shard", wr_hash=ext.report.hash().hex())
                #     asyncio.create_task(assurer._req_shard(ext))

                # TODO: Test Auditing & Refining with PJ
                # # Start Auditing for new block received
                # audit_engine = AuditEngine()
                # asyncio.create_task(audit_engine.run(block, newly_avail_wrs))

                # TODO: Remove Direct Finality
                # NOTE: We are setting instant finality here, this is to be updated once GRANDPA is implemented
                Finality.finalise(header_hash, _set.main_db, True)

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
                True
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
    return state
