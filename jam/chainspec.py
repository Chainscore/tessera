"""JAM protocol configuration."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ChainSpec(Enum):
    """Chain specification types."""

    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    XLARGE = "xlarge"
    XLARGE2 = "2xlarge"
    XLARGE3 = "3xlarge"
    FULL = "full"


@dataclass
class JamConfig:
    """JAM protocol configuration."""

    chain: ChainSpec
    num_validators: int
    num_cores: int
    slot_duration: int
    epoch_duration: int
    ticket_submission_end: int
    contest_duration: int
    tickets_per_validator: int
    max_tickets_per_extrinsic: int
    rotation_period: Optional[int]

    @classmethod
    def tiny(cls) -> "JamConfig":
        """Create tiny chain configuration."""
        return cls(
            chain=ChainSpec.TINY,
            num_validators=6,
            num_cores=2,
            slot_duration=6,
            epoch_duration=12,
            ticket_submission_end=10,
            contest_duration=10,
            tickets_per_validator=3,
            max_tickets_per_extrinsic=3,
            rotation_period=4,
        )

    @classmethod
    def small(cls) -> "JamConfig":
        """Create small chain configuration."""
        return cls(
            chain=ChainSpec.SMALL,
            num_validators=24,
            num_cores=8,
            slot_duration=6,
            epoch_duration=36,
            ticket_submission_end=30,
            contest_duration=30,
            tickets_per_validator=2,
            max_tickets_per_extrinsic=3,
            rotation_period=None,  # TODO
        )

    @classmethod
    def medium(cls) -> "JamConfig":
        """Create medium chain configuration."""
        return cls(
            chain=ChainSpec.MEDIUM,
            num_validators=48,
            num_cores=16,
            slot_duration=6,
            epoch_duration=60,
            ticket_submission_end=50,
            contest_duration=50,
            tickets_per_validator=2,
            max_tickets_per_extrinsic=3,
            rotation_period=None,  # TODO
        )

    @classmethod
    def large(cls) -> "JamConfig":
        """Create large chain configuration."""
        return cls(
            chain=ChainSpec.LARGE,
            num_validators=96,
            num_cores=32,
            slot_duration=6,
            epoch_duration=120,
            ticket_submission_end=100,
            contest_duration=100,
            tickets_per_validator=2,
            max_tickets_per_extrinsic=3,
            rotation_period=None,  # TODO
        )

    @classmethod
    def xlarge(cls) -> "JamConfig":
        """Create xlarge chain configuration."""
        return cls(
            chain=ChainSpec.XLARGE,
            num_validators=192,
            num_cores=64,
            slot_duration=6,
            epoch_duration=240,
            ticket_submission_end=200,
            contest_duration=200,
            tickets_per_validator=2,
            max_tickets_per_extrinsic=3,
            rotation_period=None,  # TODO
        )

    @classmethod
    def xlarge2(cls) -> "JamConfig":
        """Create 2xlarge chain configuration."""
        return cls(
            chain=ChainSpec.XLARGE2,
            num_validators=384,
            num_cores=128,
            slot_duration=6,
            epoch_duration=300,
            ticket_submission_end=250,
            contest_duration=250,
            tickets_per_validator=2,
            max_tickets_per_extrinsic=16,
            rotation_period=None,  # TODO
        )

    @classmethod
    def xlarge3(cls) -> "JamConfig":
        """Create 3xlarge chain configuration."""
        return cls(
            chain=ChainSpec.XLARGE3,
            num_validators=576,
            num_cores=192,
            slot_duration=6,
            epoch_duration=600,
            ticket_submission_end=500,
            contest_duration=500,
            tickets_per_validator=2,
            max_tickets_per_extrinsic=16,
            rotation_period=None,  # TODO
        )

    @classmethod
    def full(cls) -> "JamConfig":
        """Create full chain configuration."""
        return cls(
            chain=ChainSpec.FULL,
            num_validators=1023,
            num_cores=341,
            slot_duration=6,
            epoch_duration=600,
            ticket_submission_end=500,
            contest_duration=500,
            tickets_per_validator=2,
            max_tickets_per_extrinsic=16,
            rotation_period=10,
        )

    @classmethod
    def from_chain(cls, chain: str) -> "JamConfig":
        """Create configuration from chain name."""
        chain_map = {
            ChainSpec.TINY.value: cls.tiny,
            ChainSpec.SMALL.value: cls.small,
            ChainSpec.MEDIUM.value: cls.medium,
            ChainSpec.LARGE.value: cls.large,
            ChainSpec.XLARGE.value: cls.xlarge,
            ChainSpec.XLARGE2.value: cls.xlarge2,
            ChainSpec.XLARGE3.value: cls.xlarge3,
            ChainSpec.FULL.value: cls.full,
        }
        if chain not in chain_map:
            raise ValueError(f"Unknown chain spec: {chain}")
        return chain_map[chain]()


# Default to tiny chain if not specified
DEFAULT_CHAIN = "tiny"
# Load chain spec from environment variable
CHAIN_SPEC = os.environ.get("JAM_CHAIN_SPEC", DEFAULT_CHAIN)

# Create config from chain spec
chain_config = JamConfig.from_chain(CHAIN_SPEC)
