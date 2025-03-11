from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest

from jam.ring_vrf.curve.specs.bandersnatch import (
    Bandersnatch_TE_Curve,
    BandersnatchParams,
    BandersnatchPoint,
)

# Test data paths
TEST_DATA_DIR = Path("tests/unit/vrf/data")
ARK_VRF_DIR = TEST_DATA_DIR / "ark-vrf"
COLORFUL_NOTION_DIR = TEST_DATA_DIR / "colorful-notion"


def load_test_vectors(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load test vectors from a JSON file.

    Args:
        file_path: Path to test vector file

    Returns:
        List of test vectors

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(file_path, "r") as f:
        return json.load(f)


def create_public_key(secret_key_hex: str) -> BandersnatchPoint:
    """
    Create public key point from secret key hex string.

    Args:
        secret_key_hex: Hex string of secret key

    Returns:
        BandersnatchPoint: Public key point
    """
    # Create generator point
    generator = BandersnatchPoint(
        BandersnatchParams.GENERATOR_X, BandersnatchParams.GENERATOR_Y
    )

    # Convert secret key to scalar
    secret_scalar = (
        int.from_bytes(bytes.fromhex(secret_key_hex), "little")
        % Bandersnatch_TE_Curve.ORDER
    )

    # Compute public key
    return generator * secret_scalar


class TestBandersnatchEd:
    """Test suite for Bandersnatch Edwards curve operations."""

    @pytest.mark.parametrize("test_file", ARK_VRF_DIR.glob("bandersnatch_ed*.json"))
    @pytest.mark.skipif("RUNALL" not in os.environ, reason="takes too long")
    def test_public_key_generation(self, test_file: Path):
        """
        Test public key generation against test vectors.

        Args:
            test_file: Path to test vector file
        """
        vectors = load_test_vectors(test_file)

        for i, vector in enumerate(vectors, 1):
            # Generate public key
            public_key = create_public_key(vector["sk"])
            public_key_hex = public_key.point_to_string().hex()

            # Verify against test vector
            assert (
                public_key_hex == vector["pk"]
            ), f"Failed on vector {i} in {test_file.name}"
            print(f"✅ Passed vector {i} of {test_file.name}")


class TestBandersnatchSeals:
    """Test suite for Bandersnatch Seals operations."""

    @pytest.mark.parametrize("test_file", COLORFUL_NOTION_DIR.glob("*.json"))
    @pytest.mark.skipif("RUNALL" not in os.environ, reason="takes too long")
    def test_public_key_generation(self, test_file: Path):
        """
        Test public key generation against Seals test vectors.

        Args:
            test_file: Path to test vector file
        """
        vector = load_test_vectors(test_file)

        # Generate public key
        public_key = create_public_key(vector["bandersnatch_priv"])
        public_key_hex = public_key.point_to_string().hex()

        # Verify against test vector
        assert (
            public_key_hex == vector["bandersnatch_pub"]
        ), f"Failed on {test_file.name}"
        print(f"✅ Passed {test_file.name}")


@pytest.mark.parametrize(
    "x,y,expected",
    [
        (0, 1, True),  # Identity point
        (
            BandersnatchParams.GENERATOR_X,
            BandersnatchParams.GENERATOR_Y,
            True,
        ),  # Generator
        (0, 0, False),  # Invalid point
    ],
)
def test_point_validation(x: int, y: int, expected: bool):
    """
    Test point validation on curve.

    Args:
        x: x-coordinate
        y: y-coordinate
        expected: Whether point should be valid
    """
    if expected:
        point = BandersnatchPoint(x, y)
        assert point.is_on_curve()
    else:
        with pytest.raises(ValueError):
            BandersnatchPoint(x, y)


def test_point_operations():
    """Test basic point operations."""
    # Create generator point
    G = BandersnatchPoint(
        BandersnatchParams.GENERATOR_X, BandersnatchParams.GENERATOR_Y
    )

    # Test identity
    I = BandersnatchPoint(0, 1)
    assert G + I == G
    assert I + G == G

    # Test addition
    P = G * 2
    Q = G + G
    assert P == Q

    # Test subtraction
    R = P - G
    assert R == G

    # Test negation
    assert G + (-G) == I
