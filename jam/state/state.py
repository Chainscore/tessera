import json
from typing import Type

from tsrkit_types import Dictionary

from jam.merklization import BMRFunctions
from rockstore import RockStore
from jam.state.accounts import DeltaView
from jam.state.ghost import GhostState
from jam.state.merkle import StateTrie
from jam.state.utils import construct_state_key
from tsrkit_types.bytes import Bytes
from tsrkit_types.itf.codable import Codable
from jam.types import Block, Hash, Alpha, Eta, Nu, Pi, Psi, Kappa, Lambda_, Rho, Tau, Chi, Iota, Xi, Beta, Phi, Gamma
from jam.config.logging import get_logger, log_performance

logger = get_logger("import")


def make_state_prop(state_key: int, cl: Type[Codable]):
    def fget(self):
        raw = self.DB.get(bytes(construct_state_key(state_key)))
        if raw is None:
            logger.error(
                "State component missing from database",
                component=cl.__name__,
                state_key=state_key
            )
            raise ValueError(f"State component missing from DB: {cl.__name__}")
        return cl.decode_from(raw)[0]

    def fset(self, value):
        k, v = construct_state_key(state_key), value.encode()
        self.TRIE.update(k, Bytes(v))
        self.DB.put(bytes(k), v)
        
        logger.debug(
            "State component updated",
            component=cl.__name__,
            state_key=state_key,
            value_size=len(v)
        )

    return property(fget, fset)

class State:
    """
    State implementation that uses dynamic components fetched from Db
    Here we retain and update merkle trie as cache
    """
    DB: RockStore
    TRIE: StateTrie

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
        return DeltaView(self.DB, self.TRIE)

    def __init__(self, db = None, trie = None):
        self.DB = db
        self.TRIE = trie
        
        logger.debug(
            "State instance initialized",
            has_db=db is not None,
            has_trie=trie is not None
        )

    @property
    def root(self):
        return self.TRIE.root_hash

    def transition(self, block: Block):
        """
        Main state transition function. Takes in the current state and the incoming block, returns the transitioned state

        Args:
            block: Incoming block
        """
        from jam.accumulation.accumulation import Accumulation
        from jam.report.reporting import Reporting
        from jam.authorization.authorization import Authorization
        from jam.recent_history.recent_history import RecentHistory
        from jam.consensus.safrole.safrole import Safrole
        from jam.assurances.assurances import Assurances
        from jam.disputes.disputes import Disputes
        from jam.preimages.preimages import Preimages
        from jam.statistics.statistics import Statistics

        block_context = {
            "block_slot": int(block.header.slot),
            "parent_hash": block.header.parent.hex()[:16] + "...",
            "state_root": block.header.parent_state_root.hex()[:16] + "...",
            "extrinsic_hash": block.header.extrinsic_hash.hex()[:16] + "...",
            "author_index": int(block.header.author_index)
        }
        
        logger.info(
            "Starting state transition",
            **block_context
        )

        with log_performance(logger, "state_transition", **block_context):
            # TODO: Validate block headers
            # Epoch markers - make sure eta0_1 are the same as current etas
            # Tickets mark - make sure ticket.py are valid, present in gamma_a and outside in sequenced
            # Offenders mark - make sure offenders are present in psi.offenders

            logger.debug(
                "Updating beta with previous block state root",
                **block_context
            )
            
            beta = self.beta
            # Step 1
            if len(beta):
                beta[-1].state_root = block.header.parent_state_root
            self.beta = beta

            # Disputes
            logger.debug("Processing disputes", **block_context)
            with log_performance(logger, "disputes_transition", **block_context):
                Disputes.transition(self, block)
            
            # Work package hashes form Nu and Xi
            logger.debug("Gathering known work packages", **block_context)
            known_packages = [
                queue_el.report.context.prerequisites
                for epoch_queue in self.nu
                for queue_el in epoch_queue
            ]
            known_packages.extend([
                wps
                for deps in self.xi
                for wps in deps
            ])
            
            logger.debug(
                "Known packages collected",
                package_count=len(known_packages),
                **block_context
            )
            
            # Reporting
            logger.debug("Processing reporting", **block_context)
            with log_performance(logger, "reporting_transition", **block_context):
                Reporting.transition(self, block, known_packages=known_packages)
            
            # Assurances
            logger.debug("Processing assurances", **block_context)
            with log_performance(logger, "assurances_transition", **block_context):
                _, newly_avail_wrs = Assurances.transition(self, block)
            
            logger.debug(
                "Assurances processed",
                newly_available_count=len(newly_avail_wrs) if newly_avail_wrs else 0,
                **block_context
            )

            # Accumulation
            logger.debug("Processing accumulation", **block_context)
            with log_performance(logger, "accumulation_transition", **block_context):
                _, commitment_map = Accumulation.transition(self, block, newly_avail_wrs=newly_avail_wrs)
            
            logger.debug(
                "Accumulation processed",
                commitment_count=len(commitment_map) if commitment_map else 0,
                **block_context
            )
            
            # Authorization
            logger.debug("Processing authorization", **block_context)
            with log_performance(logger, "authorization_transition", **block_context):
                Authorization.transition(self, block)
            
            # Recent History
            logger.debug("Processing recent history", **block_context)
            history_merkle = BMRFunctions().wb_merkle_fn(
                sorted([Bytes(comm[0].encode() + comm[1].encode()) for comm in commitment_map]), 
                Hash.keccak256
            )
            with log_performance(logger, "recent_history_transition", **block_context):
                RecentHistory.transition(self, block, history_merkle)
            
            # Preimages
            logger.debug("Processing preimages", **block_context)
            with log_performance(logger, "preimages_transition", **block_context):
                Preimages.transition(self, block)
            
            # Statistics
            logger.debug("Processing statistics", **block_context)
            with log_performance(logger, "statistics_transition", **block_context):
                Statistics.transition(self, block, newly_avail_wrs)
            
            # Safrole
            logger.debug("Processing safrole consensus", **block_context)
            vrf_output = Safrole.vrf_output(block.header.entropy_source)
            with log_performance(logger, "safrole_transition", **block_context):
                Safrole.transition(self, block, vrf_output)
        
        logger.info(
            "State transition completed successfully",
            **block_context,
            final_state_root=self.root.hex()[:16] + "..."
        )

state = State()

def set_state(new_state: State):
    global state
    
    logger.info(
        "Global state updated",
        has_db=new_state.DB is not None,
        has_trie=new_state.TRIE is not None,
        state_root=new_state.root.hex()[:16] + "..." if new_state.TRIE else None
    )
    
    state = new_state
    return state

def setup_state(db: RockStore, genesis: GhostState | str = "dev-spec.json"):
    logger.info(
        "Setting up state from genesis",
        genesis_type=type(genesis).__name__,
        genesis_source=genesis if isinstance(genesis, str) else "GhostState"
    )
    
    if isinstance(genesis, str):
        logger.debug(
            "Loading genesis from JSON file",
            genesis_file=genesis
        )
        genesis_json = json.load(open(genesis))
        data = Dictionary[Bytes, Bytes].from_json(genesis_json["genesis_state"])
    else:
        logger.debug("Transforming GhostState to genesis data")
        data = genesis.transform()
    
    logger.debug(
        "Building state trie from genesis data",
        data_entries=len(data)
    )
    
    trie = StateTrie()
    trie.merkelize(data, db)

    new_state = State(db, trie)
    
    logger.info(
        "State setup completed",
        state_root=new_state.root.hex()[:16] + "...",
        data_entries=len(data)
    )
    
    global state
    state = new_state
    return state