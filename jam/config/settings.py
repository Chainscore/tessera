from pathlib import Path
from jam.utils.constants import (
    SLOT_PERIOD, EPOCH_LENGTH, VALIDATOR_COUNT,
    MAX_SERVICE_CODE_SIZE
)

class Settings():
    # Node settings
    NODE_NAME: str = "JAM-Node"
    NODE_ID: str | None = None
    
    # Network settings
    LISTEN_ADDRESS: str = "0.0.0.0"
    LISTEN_PORT: int = 30333
    MAX_PEERS: int = 50
    
    # Database settings
    DB_PATH: Path = Path("data/db")
    
    # Consensus settings
    EPOCH_LENGTH: int = EPOCH_LENGTH
    SLOT_DURATION: int = SLOT_PERIOD
    VALIDATOR_COUNT: int = VALIDATOR_COUNT
    
    # PVM settings
    PVM_MAX_MEMORY: int = 2**32  # 4GB
    PVM_STACK_SIZE: int = 2**20  # 1MB
    
    # Service settings
    MAX_SERVICE_SIZE: int = MAX_SERVICE_CODE_SIZE
    MAX_PREIMAGE_SIZE: int = MAX_SERVICE_CODE_SIZE
    
    # Execution settings
    MAX_REFINE_GAS: int = 500_000_000
    MAX_ACCUMULATE_GAS: int = 100_000
    
    class Config:
        env_prefix = "JAM_"
        env_file = ".env"

settings = Settings()