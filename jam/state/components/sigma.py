from dataclasses import dataclass

from jam.state.components.alpha import Alpha
from jam.state.components.beta import Beta
from jam.state.components.chi import Chi
from jam.state.components.eta import Eta
from jam.state.components.gamma import Gamma
from jam.state.components.delta import Delta
from jam.state.components.iota import Iota
from jam.state.components.kappa import Kappa
from jam.state.components.lambada import Lambada
from jam.state.components.pi import Pi
from jam.state.components.psi import Psi
from jam.state.components.rho import Rho
from jam.state.components.phi import Phi
from jam.state.components.tau import Tau
from jam.state.components.theta import Theta
from jam.state.components.xi import Xi
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass

@decodable_dataclass
@dataclass
class Sigma(Codable):
    alpha: Alpha
    beta: Beta
    gamma: Gamma
    delta: Delta
    eta: Eta
    iota: Iota
    kappa: Kappa
    lambada: Lambada
    rho: Rho
    tau: Tau
    phi: Phi
    chi: Chi
    psi: Psi
    pi: Pi
    theta: Theta
    xi: Xi