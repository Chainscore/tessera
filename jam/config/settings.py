# jam/config/settings.py

from pydantic import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
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
    EPOCH_LENGTH: int = 600  # slots
    SLOT_DURATION: int = 6   # seconds
    VALIDATOR_COUNT: int = 1023
    
    # PVM settings
    PVM_MAX_MEMORY: int = 2**32  # 4GB
    PVM_STACK_SIZE: int = 2**20  # 1MB
    
    # Service settings
    MAX_SERVICE_SIZE: int = 4_000_000  # bytes
    MAX_PREIMAGE_SIZE: int = 4_000_000  # bytes
    
    # Execution settings
    MAX_REFINE_GAS: int = 500_000_000
    MAX_ACCUMULATE_GAS: int = 100_000
    
    class Config:
        env_prefix = "JAM_"
        env_file = ".env"

settings = Settings()