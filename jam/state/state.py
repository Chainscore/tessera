from jam.state.components.sigma import Sigma
from jam.types.block import Block
from jam.state.utils.key_constructor import construct_state_key
from jam.state.merkle import StateMerkle
from jam.types.base.sequences.bytes import ByteArray32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.protocol.crypto import Hash
from jam.authorization.authorization import Authorization
from jam.recent_history.recent_history import RecentHistory
from jam.consensus.safrole.safrole import Safrole
from jam.assurances.assurances import Assurances
from jam.disputes.disputes import Disputes
from jam.preimages.preimages import Preimages
from jam.statistics.statistics import Statistics



class State(Sigma):
    """State implementation that adds Merklization to Sigma"""

    def __init__(self, **kwargs):
        """Initialize state with component kwargs"""
        super().__init__(**kwargs)
        self._merkle = StateMerkle(Hash.blake2b)

    def transform(self) -> dict:
        """Transform the state into a dictionary as defined in D.2"""
        # TODO - To add service-related state components when they Section 9 is implemented
        return {
            construct_state_key(1): Bytes(self.alpha.encode()),
            construct_state_key(2): Bytes(self.beta.encode()),
            construct_state_key(3): Bytes(self.gamma.encode()),
            construct_state_key(4): Bytes(self.delta.encode()),
            construct_state_key(5): Bytes(self.psi.encode()),
            construct_state_key(6): Bytes(self.eta.encode()),
            construct_state_key(7): Bytes(self.iota.encode()),
            construct_state_key(8): Bytes(self.kappa.encode()),
            construct_state_key(9): Bytes(self.lambada.encode()),
            construct_state_key(10): Bytes(self.rho.encode()),
            construct_state_key(11): Bytes(self.tau.encode()),
            construct_state_key(12): Bytes(self.chi.encode()),
            construct_state_key(13): Bytes(self.pi.encode()),
            construct_state_key(14): Bytes(self.theta.encode()),
            construct_state_key(15): Bytes(self.xi.encode()),
        }

    def generate_root(self) -> ByteArray32:
        """Generate the root hash of the state"""
        return self._merkle.merkelize(self.transform())

    def get_merkle_nodes(self) -> dict:
        """Get all nodes in the state Merkle trie"""
        return self._merkle.get_nodes()

    def master_transition_state(self, block : Block):
        """
               Master transition state

               args accepted
                pre_state: state before transition

                block: block

               returns new_state
                """

        # section 11 (assurance and the Reporting)
        genesis_state = self.value
        block_production_state = Safrole.transition(genesis_state, block)
        recent_block_history_state = RecentHistory.transition(block_production_state, block, ByteArray32([0] * 32))
        authorization_state = Authorization.transition(recent_block_history_state, block)
        disputes_state = Disputes.transition(authorization_state, block)
        assurance_state = Assurances.transition(disputes_state, block)
        # reporting_state = Report.transition(assurance_state, block) ## TODO: update with latest state oreders.
        # accumulation_state = accumulate.transition(reporting_state, block)
        preimage_state = Preimages.transition(assurance_state, block)
        statistics_state = Statistics.transition(preimage_state, block)

        self.value = statistics_state