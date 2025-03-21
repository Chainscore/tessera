from dataclasses import dataclass

import plyvel
import json

from jam.state.components.delta import AccountData, AccountStorage, PreImageLookup, LookupTimestamps, Delta
from jam.state.components.pi import Pi
from jam.db.types import DunaGamme, DunaState, DunaChi, DunaDelta
from jam.state.components.alpha import Alpha
from jam.state.components.eta import Eta
from jam.state.components.iota import Iota
from jam.state.components.kappa import Kappa
from jam.state.components.lambda_ import Lambda_
from jam.state.components.nu import Nu
from jam.state.components.phi import Phi
from jam.state.components.psi import Psi
from jam.state.components.rho import Rho
from jam.state.components.tau import Tau
from jam.state.components.xi import Xi
# from tests.integration.jam import DunaState

from jam.state.state import State
from jam.types import Bytes
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.utils.json import JsonSerde
from tests.fixtures.dummy_state import create_dummy_state
from tests.unit.recent_history.types import BetaInput
from tests.unit.statistics.types import Pi as TestPi

from pathlib import Path



@decodable_dataclass
@dataclass
class TestState(Codable, JsonSerde):
    alpha: Alpha
    varphi: Phi
    beta: BetaInput
    gamma: DunaGamme
    psi: Psi
    eta: Eta
    iota: Iota
    kappa: Kappa
    lambda_: Lambda_
    rho: Rho
    tau: Tau
    chi: DunaChi
    pi: TestPi
    theta: Nu
    xi: Xi
    accounts: DunaDelta




# Construct relative path from project root

genesis_file = "tests/integration/jam-duna/state_snapshots/genesis.json"
with open(genesis_file) as file:
    genesis_data = json.loads(file.read())
    try:
        tc = DunaState.from_json(genesis_data)
        print(f"Decoded {file}")
    except Exception as e:
        print(f"❌ Failed to decode {file}: {e}")


initial_state = tc.to_state()
if __name__ == "__main__":
    transform_state=initial_state.transform()
    for i in transform_state:
        print(i)

# Open RocksDB
db = plyvel.DB("mydb", create_if_missing=True)

# Sample dictionary
data = transform_state
test_data = {}

for key, value in data.items():
    test_data[Bytes(key).hex()] = Bytes(value).hex()



# Convert dictionary to JSON string
json_data = json.dumps(test_data)

# Store in RocksDB
db.put(b'user:1', json_data.encode())

# Retrieve from RocksDB
retrieved_data = db.get(b'user:1')
# if retrieved_data:
#     dict_data = json.loads(retrieved_data.decode())
#     for key in dict_data:
#         print(key)

db.close()
