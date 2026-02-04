import os
from typing import Optional
from pydantic import BaseModel, Field
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda *args, **kwargs: None

class NodeConfig(BaseModel):
    """
    Configuration for the Jam Node.
    Reads from environment variables with prefix JAM_ and .env file.
    """
    NODE_NAME: str = "jam-node"
    PORT: int = 40000
    SEED: str = "0"
    HOST: str = "0.0.0.0"
    
    # RPC
    RPC_FLAG: bool = True
    RPC_PORT: int = 19800
    RPC_HOST: str = "0.0.0.0"
    
    # Storage
    DATA_PATH: Optional[str] = None
    
    # Telemetry
    TELEMETRY: Optional[str] = None
    
    # Logging
    LOG_THEME: str = "bitcoin"
    LOG_LEVEL: str = "INFO"
    
    # Features
    BUILDER: bool = False
    VALIDATOR: bool = True

    def __init__(self, _env_file: Optional[str] = ".env", **kwargs):
        # Load env file if provided
        if _env_file and os.path.exists(_env_file):
            load_dotenv(_env_file, override=True)
        else:
            # Try default .env
            load_dotenv(".env")
            
        # Collect values from env vars (JAM_ prefix takes precedence over defaults, but kwargs take precedence over env)
        env_values = {}
        target_fields = self.model_fields
        
        for field_name in target_fields:
            env_key = f"JAM_{field_name}"
            val = os.environ.get(env_key)
            if val is not None:
                # Basic type casting
                field_type = target_fields[field_name].annotation
                if field_type is bool:
                    env_values[field_name] = val.lower() in ('true', '1', 'yes')
                elif field_type is int:
                    env_values[field_name] = int(val)
                else:
                    env_values[field_name] = val
        
        # Also support non-prefixed env vars if defined in legacy .env files (like PORT, SEED)
        # This emulates old behavior and pydantic-settings partially
        legacy_keys = ["PORT", "SEED", "NODE_NAME", "HOST", "RPC_PORT", "RPC_HOST"]
        for key in legacy_keys:
            if key in target_fields and getattr(env_values, key, None) is None:
                 val = os.environ.get(key)
                 if val is not None:
                      env_values[key] = val
                      if target_fields[key].annotation is int:
                           env_values[key] = int(val)

        # Merge: kwargs > env_values > defaults (handled by pydantic)
        final_values = {**env_values, **kwargs}
        
        super().__init__(**final_values)
