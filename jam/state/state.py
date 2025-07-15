import json
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from jam.finality.finality import Finality
from jam.error import JamError
from jam.utils.merkle import BMRFunctions
from rockstore import RockStore
from jam.state.accounts import DeltaView
from jam.state.ghost import GhostState
from jam.utils.trie.merkle import StateTrie
from jam.state.storage import StateStorage
from jam.state.utils import construct_state_key
from tsrkit_types import Bytes, Codable, Dictionary, TypedVector
from jam.types import (
    Hash,
    Alpha,
    Eta,
    Nu,
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

logger = get_logger("import")


def make_state_prop(state_key: int, cl: Type[Codable]):
    def fget(self):
        raw = self.store.get(construct_state_key(state_key))
        if raw is None:
            raise ValueError(f"State component missing from DB: {cl.__name__}")
        return cl.decode_from(raw)[0]

    def fset(self, value):
        k, v = construct_state_key(state_key), value.encode()
        self.store.put(bytes(k), v)
        logger.debug(
            "State component updated",
            component=cl.__name__,
            state_key=state_key,
            value_size=len(v),
        )

    return property(fget, fset)


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
    nu = make_state_prop(14, Nu)
    xi = make_state_prop(15, Xi)

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
        db = RockStore(settings._data_path + "/state", options={"read_only": True})
        # Load past updates
        cache = state.store._load_updates(header_hash)

        return State(StateStorage(trie, db, cache))

    def settle(self, header_hash: HeaderHash):
        """Settles a set of state changes cached in store. Marks off the settlement with an unique header hash"""
        from jam.settings import settings

        self.store.save_n_clear_cache(header_hash, settings.main_db)

    def _force_transition(self, block: Block):
        # 1. Push auth hash of every WR to self.alpha[0:1]
        return self.transition(block)

    def transition(self, block: Block):
        """
        Main state transition function. Takes in the current state and the incoming block, returns the transitioned state

        Args:
            block: Incoming block
        """
        if self._lock:
            logger.error("Lock detected, skipping transition")
            return

        self._lock = True

        from jam.state.transitions import Accumulation, Reporting, Authorization, RecentHistory, Safrole, Assurances, Disputes, Preimages, Statistics
        from jam.settings import settings as _set
        from jam.finality.finality import Finality

        try:
            header_hash = HeaderHash(block.header.hash())
            logger.info(
                "Starting state transition on block",
                header_hash=header_hash.hex(),
                block_slot=int(block.header.slot),
                parent_hash=block.header.parent.hex()[:16] + "...",
                state_root=block.header.parent_state_root.hex()[:16] + "...",
                author_index=int(block.header.author_index),
            )

            # TODO: Validate block headers
            # Epoch markers - make sure eta0_1 are the same as current etas
            # Tickets mark - make sure ticket.py are valid, present in gamma_a and outside in sequenced
            # Offenders mark - make sure offenders are present in psi.offenders
            if block.header.slot == 0:
                logger.warning("Found genesis block, skipping", hh=header_hash.hex())
                self._lock = False
                return

            if _set.main_db.get(Block.get_storage_key_block(header_hash)) is not None:
                logger.warning("Duplicate block found, skipping", hh=header_hash.hex())
                self._lock = False
                return

            pre_state = self.load()

            beta = self.beta
            # Step 1
            if len(beta):
                beta[-1].state_root = block.header.parent_state_root
            self.beta = beta

            # Disputes
            logger.debug("Processing disputes...")
            Disputes.transition(pre_state, self, block)

            # Reporting
            logger.debug("Processing reporting...")
            Reporting.transition(pre_state, self, block, [])

            # Assurances
            logger.debug("Processing assurances...")
            _, newly_avail_wrs = Assurances.transition(pre_state, self, block)

            # Accumulation
            logger.debug(
                "Processing accumulation...", newly_available_count=len(newly_avail_wrs)
            )
            _, commitment_map = Accumulation.transition(
                pre_state, self, block, newly_avail_wrs=newly_avail_wrs
            )

            # Authorization
            logger.debug("Processing authorization...")
            Authorization.transition(pre_state, self, block)

            # Recent History
            logger.debug(
                "Processing recent history...", commitment_count=len(commitment_map)
            )
            history_merkle = BMRFunctions().wb_merkle_fn(
                TypedVector[Bytes[32]](sorted(
                    [
                        Bytes(comm[0].encode() + comm[1].encode())
                        for comm in commitment_map
                    ]
                )),
                Hash.keccak256,
            )
            RecentHistory.transition(pre_state, self, block, history_merkle)

            # Preimages
            logger.debug("Processing preimages...")
            Preimages.transition(pre_state, self, block)

            # Statistics
            logger.debug("Processing statistics...")
            Statistics.transition(pre_state, self, block, newly_avail_wrs)

            # Safrole
            logger.debug("Processing safrole...")
            vrf_output = Safrole.get_vrf_output(block.header.entropy_source)
            Safrole.transition(pre_state, self, block, vrf_output)

            state.settle(header_hash)

            logger.info(
                "Block imported!",
                header=header_hash.hex()[:16] + "...",
                timeslot=self.tau,
                final_state_root=self.root.hex()[:16] + "...",
            )

            block.save(_set.main_db)
            # Set local chain head to produced block
            Finality.set_head(header_hash, _set.main_db)
            # NOTE: We are setting instant finality here, this is to be updated once GRANDPA is implemented
            Finality.finalise(header_hash, _set.main_db)

            block.extrinsic.clear_from_stores()

        except JamError as jam_e:
            logger.error(
                "Invalid block", error=jam_e,
                hh=block.header.hash().hex(),
                slot=block.header.slot,
            )
            self.store.clear()

        self._lock = False
        return


state = State(None)


def set_state(new_state: State):
    global state

    logger.info("Global state updated")

    state = new_state
    return state


def setup_state(
    state_db: RockStore, genesis: GhostState | str | dict = "dev-spec.json"
):
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
