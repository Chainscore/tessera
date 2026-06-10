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

    name: str
    chain: ChainSpec
    preimage_expunge_period: int
    num_validators: int
    num_cores: int
    slot_duration: int
    epoch_duration: int
    ticket_submission_end: int
    contest_duration: int
    tickets_per_validator: int
    max_tickets_per_extrinsic: int
    rotation_period: Optional[int]
    erasure_coding_original_shards: int  # RECOVERY THRESHOLD
    erasure_coding_recovery_shards: int
    recovery_threshold: int
    num_ec_pieces_per_segment: int
    max_block_gas: int
    max_refine_gas: int
    audit_report_assign: int
    lookup_anchor_max_age: int

    @staticmethod
    def _scaled_rotation_period(epoch_duration: int) -> int:
        return max(4, epoch_duration // 60)

    @staticmethod
    def _scaled_audit_report_assign(num_cores: int) -> int:
        return max(2, min(10, (num_cores * 10 + 340) // 341))

    @classmethod
    def tiny(cls) -> "JamConfig":
        """Create tiny chain configuration."""
        return cls(
            name="tiny",
            chain=ChainSpec.TINY,
            num_validators=6,
            num_cores=2,
            slot_duration=6,
            epoch_duration=12,
            ticket_submission_end=10,
            contest_duration=10,
            tickets_per_validator=4,
            max_tickets_per_extrinsic=3,
            rotation_period=4,
            erasure_coding_original_shards=3,
            erasure_coding_recovery_shards=3,
            recovery_threshold=3,
            preimage_expunge_period=32,
            num_ec_pieces_per_segment=684,
            max_block_gas=20000000,
            max_refine_gas=1000000000,
            audit_report_assign=2,
            lookup_anchor_max_age=24
        )

    @classmethod
    def small(cls) -> "JamConfig":
        """Create small chain configuration."""
        return cls(
            name="small",
            chain=ChainSpec.SMALL,
            num_validators=24,
            num_cores=8,
            slot_duration=6,
            epoch_duration=36,
            ticket_submission_end=30,
            contest_duration=30,
            tickets_per_validator=3,
            max_tickets_per_extrinsic=3,
            rotation_period=cls._scaled_rotation_period(36),
            erasure_coding_original_shards=9,
            erasure_coding_recovery_shards=15,
            recovery_threshold=9,
            preimage_expunge_period=32,
            num_ec_pieces_per_segment=228,
            max_block_gas=20000000,
            max_refine_gas=1000000000,
            audit_report_assign=cls._scaled_audit_report_assign(8),
            lookup_anchor_max_age=14400
        )

    @classmethod
    def medium(cls) -> "JamConfig":
        """Create medium chain configuration."""
        return cls(
            name="medium",
            chain=ChainSpec.MEDIUM,
            num_validators=48,
            num_cores=16,
            slot_duration=6,
            epoch_duration=60,
            ticket_submission_end=50,
            contest_duration=50,
            tickets_per_validator=3,
            max_tickets_per_extrinsic=3,
            rotation_period=cls._scaled_rotation_period(60),
            erasure_coding_original_shards=12,
            erasure_coding_recovery_shards=36,
            recovery_threshold=12,
            preimage_expunge_period=32,
            num_ec_pieces_per_segment=171,
            max_block_gas=20000000,
            max_refine_gas=1000000000,
            audit_report_assign=cls._scaled_audit_report_assign(16),
            lookup_anchor_max_age=14400
        )

    @classmethod
    def large(cls) -> "JamConfig":
        """Create large chain configuration."""
        return cls(
            name="large",
            chain=ChainSpec.LARGE,
            num_validators=96,
            num_cores=32,
            slot_duration=6,
            epoch_duration=120,
            ticket_submission_end=100,
            contest_duration=100,
            tickets_per_validator=3,
            max_tickets_per_extrinsic=3,
            rotation_period=cls._scaled_rotation_period(120),
            erasure_coding_original_shards=27,
            erasure_coding_recovery_shards=69,
            recovery_threshold=27,
            preimage_expunge_period=32,
            num_ec_pieces_per_segment=76,
            max_block_gas=20000000,
            max_refine_gas=1000000000,
            audit_report_assign=cls._scaled_audit_report_assign(32),
            lookup_anchor_max_age=14400
        )

    @classmethod
    def xlarge(cls) -> "JamConfig":
        """Create xlarge chain configuration."""
        return cls(
            name="xlarge",
            chain=ChainSpec.XLARGE,
            num_validators=192,
            num_cores=64,
            slot_duration=6,
            epoch_duration=240,
            ticket_submission_end=200,
            contest_duration=200,
            tickets_per_validator=3,
            max_tickets_per_extrinsic=3,
            rotation_period=cls._scaled_rotation_period(240),
            erasure_coding_original_shards=57,
            erasure_coding_recovery_shards=135,
            recovery_threshold=57,
            preimage_expunge_period=32,
            num_ec_pieces_per_segment=36,
            max_block_gas=20000000,
            max_refine_gas=1000000000,
            audit_report_assign=cls._scaled_audit_report_assign(64),
            lookup_anchor_max_age=14400
        )

    @classmethod
    def xlarge2(cls) -> "JamConfig":
        """Create 2xlarge chain configuration."""
        return cls(
            name="2xlarge",
            chain=ChainSpec.XLARGE2,
            num_validators=384,
            num_cores=128,
            slot_duration=6,
            epoch_duration=300,
            ticket_submission_end=250,
            contest_duration=250,
            tickets_per_validator=2,
            max_tickets_per_extrinsic=16,
            rotation_period=cls._scaled_rotation_period(300),
            erasure_coding_original_shards=114,
            erasure_coding_recovery_shards=270,
            recovery_threshold=114,
            preimage_expunge_period=32,
            num_ec_pieces_per_segment=18,
            max_block_gas=20000000,
            max_refine_gas=1000000000,
            audit_report_assign=cls._scaled_audit_report_assign(128),
            lookup_anchor_max_age=14400
        )

    @classmethod
    def xlarge3(cls) -> "JamConfig":
        """Create 3xlarge chain configuration."""
        return cls(
            name="3xlarge",
            chain=ChainSpec.XLARGE3,
            num_validators=576,
            num_cores=192,
            slot_duration=6,
            epoch_duration=600,
            ticket_submission_end=500,
            contest_duration=500,
            tickets_per_validator=3,
            max_tickets_per_extrinsic=16,
            rotation_period=cls._scaled_rotation_period(600),
            erasure_coding_original_shards=171,
            erasure_coding_recovery_shards=405,
            recovery_threshold=171,
            preimage_expunge_period=32,
            num_ec_pieces_per_segment=12,
            max_block_gas=20000000,
            max_refine_gas=1000000000,
            audit_report_assign=cls._scaled_audit_report_assign(192),
            lookup_anchor_max_age=14400
        )

    @classmethod
    def full(cls) -> "JamConfig":
        """Create full chain configuration."""
        return cls(
            name="full",
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
            erasure_coding_original_shards=342,
            erasure_coding_recovery_shards=681,
            recovery_threshold=342,
            preimage_expunge_period=19200,
            num_ec_pieces_per_segment=6,
            max_block_gas=3500000000,
            max_refine_gas=5000000000,
            lookup_anchor_max_age=14400,
            audit_report_assign=10
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

# Internal cache for singleton-style lazy initialization
_chain_config_instance: Optional[JamConfig] = None

def get_chain_config() -> JamConfig:
    global _chain_config_instance
    chain = os.environ.get("JAM_CHAIN_SPEC", DEFAULT_CHAIN)
    if _chain_config_instance is None or _chain_config_instance.name != chain:
        _chain_config_instance = JamConfig.from_chain(chain)
    return _chain_config_instance

# ✅ chain_config acts like a JamConfig but loads lazily at runtime
class _ChainConfigProxy:
    def __getattr__(self, name):
        return getattr(get_chain_config(), name)

    def __repr__(self):
        return repr(get_chain_config())

# ✅ Exported name, compatible with existing imports
chain_config = _ChainConfigProxy()
