from tsrkit_types.struct import structure

from . import Alpha, Phi, Beta, Eta, Pi, Psi, Kappa, Lambda_, Rho, Tau, Chi, Iota, Omega, Xi, Gamma, Delta
from .theta import Theta


@structure
class Sigma:
    """
    Overall system state combining all components (σ). Defined in Graypaper section 4.2.

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/087601087601?v=0.7.0
    """

    # Core authorizations pool tracking allowed authorizers for each core (α ∈ C⟦H⟧:OH C)
    # Defined in section 8.1
    alpha: Alpha

    # Recent block history including block hash, state root, accumulation MMR, and work package hashes
    # Defined in section 7.1
    beta: Beta

    # Most Recent Accumulated Outputs Sequence
    # Defined in section 7.4
    theta: Theta

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

    # Validator activity statistics (blocks produced, ticket.py submitted, etc.)
    # Defined in section 13
    pi: Pi

    # Accumulation ready work-reports
    # Defined in section 12
    omega: Omega

    # History of accumulated work-reports
    # Defined in section 12
    xi: Xi
