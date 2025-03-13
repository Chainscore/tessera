from dataclasses import dataclass

from jam.state.components.alpha import Alpha
from jam.state.components.beta import Beta
from jam.state.components.chi import Chi
from jam.state.components.eta import Eta
from jam.consensus.safrole.gamma import Gamma
from jam.state.components.delta import Delta
from jam.state.components.iota import Iota
from jam.state.components.kappa import Kappa
from jam.state.components.lambda_ import Lambda_
from jam.state.components.pi import Pi
from jam.state.components.psi import Psi
from jam.state.components.rho import Rho
from jam.state.components.phi import Phi
from jam.state.components.tau import Tau
from jam.state.components.theta import Theta
from jam.state.components.xi import Xi
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.decorators import with_json_metadata
from jam.utils.json.serde import JsonSerde


@dataclass(kw_only=True)
@with_json_metadata(
    lambda_={"name": "lambda"}
)
@decodable_dataclass
class Sigma(Codable, JsonSerde):
    """Overall system state combining all components (σ). Defined in Graypaper section 4.2."""

    # Core authorizations pool tracking allowed authorizers for each core (α ∈ C⟦H⟧:OH C)
    # Defined in section 8.1
    alpha: Alpha

    # Recent block history including block hash, state root, accumulation MMR, and work package hashes
    # Defined in section 7.1
    beta: Beta

    # Safrole consensus state containing ticket accumulator (γₐ), next epoch validator keys (γₖ),
    # sealing key sequence (γₛ), and Bandersnatch root (γᵧ)
    # Defined in section 6.2
    gamma: Gamma

    # Service accounts state including smart contracts, with intermediate states (δ† and δ‡)
    # for preimage integration and accumulation
    # Defined in section 9
    delta: Delta

    # Entropy accumulator and epochal randomness (sequence of 4 hash values)
    # Defined in section 6.2
    eta: Eta

    # Queue of validator keys to be activated in future epochs
    # Defined in section 6.3
    iota: Iota

    # Currently active validator keys and metadata
    # Defined in section 6.3
    kappa: Kappa

    # Previous epoch's validator keys and metadata
    # Defined in section 6.3
    lambda_: Lambda_

    # Tracks work-reports available but not yet accumulated (has states ρ† and ρ‡)
    # Defined in section 11.1
    rho: Rho

    # Most recent block's timeslot index
    # Defined in section 6.1
    tau: Tau

    # Authorization queue that feeds into the authorization pool
    # Defined in section 8.1
    phi: Phi

    # Privileged service indices (manager, validator designator, always-accumulate services)
    # Defined in section 9.4
    chi: Chi

    # Tracks judgments on work-reports (good/bad/unknown) and validator offenses
    # Defined in section 10.1
    psi: Psi

    # Validator activity statistics (blocks produced, tickets submitted, etc.)
    # Defined in section 13
    pi: Pi

    # Accumulation queue for ready work-reports
    # Defined in section 12
    theta: Theta

    # History of accumulated work-reports
    # Defined in section 12
    xi: Xi
