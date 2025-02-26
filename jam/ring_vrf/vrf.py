from __future__ import annotations

from typing import List, Dict, Tuple, Protocol, TypeVar, Optional
from abc import ABC, abstractmethod

from .curve.point import Point
from .curve.curve import Curve
from jam.types.protocol.crypto import Hash

C = TypeVar('C', bound=Curve)
P = TypeVar('P', bound=Point)

class VRFProtocol(Protocol[C, P]):
    """Protocol defining the interface for VRF implementations."""
    
    @abstractmethod
    def prove(self, alpha: bytes, secret_key: int, additional_data: bytes) -> Tuple[P, Tuple[int, int]]:
        """Generate VRF proof."""
        ...
    
    @abstractmethod
    def verify(self, public_key: P, input_point: P, additional_data: bytes,
                output_point: P, proof: Tuple[int, int]) -> bool:
        """Verify VRF proof."""
        ...

class VRF(ABC):
    """
    Base VRF (Verifiable Random Function) implementation.
    
    This class provides the core functionality for VRF operations,
    following the IETF specification.
    """
    
    def __init__(self, curve: C):
        """
        Initialize VRF with a curve.
        
        Args:
            curve: Elliptic curve to use for VRF operations
        """
        self.curve = curve
    
    def generate_nonce(self, secret_key: int, input_point: Point) -> int:
        """
        Generate a deterministic nonce for VRF proof.
        
        Args:
            secret_key: The secret key
            input_point: The input point
            
        Returns:
            int: Generated nonce
        """
        # Hash secret key (little-endian)
        sk_encoded = secret_key.to_bytes(32, 'little')
        hashed_sk = bytes(Hash.sha512(sk_encoded))
        sk_hash = hashed_sk[32:64]  # Use second half of SHA-512 output
        
        # Concatenate with input point encoding
        point_octet = input_point.point_to_string()
        data = sk_hash + point_octet
        
        # Generate final nonce
        nonce_hash = bytes(Hash.sha512(data))
        nonce = int.from_bytes(nonce_hash, 'little')
        
        return nonce % self.curve.ORDER
    
    def challenge(
        self,
        points: List[Point],
        additional_data: bytes
    ) -> int:
        """
        Generate VRF challenge.
        
        Args:
            Y: Public key point
            I: Input point
            O: Output point
            U: First proof point
            V: Second proof point
            additional_data: Additional data to include in challenge
            
        Returns:
            int: Generated challenge
        """
        # Create challenge string
        str0 = self.curve.SUITE_STRING.encode() + bytes([0x02])
        challenge_string = str0
        
        # Add point encodings
        for P in points:
            challenge_string += P.point_to_string()
            
        # Add additional data and finalize
        hash_input = challenge_string + additional_data + bytes([0x00])
        challenge_hash = bytes(Hash.sha512(hash_input))[:32]
        
        return int.from_bytes(challenge_hash, 'big') % self.curve.ORDER
    
    @abstractmethod
    def prove(
        self,
        *args
    ) -> Tuple[Point, Tuple[int, int]]:
        """
        Generate VRF proof.
        
        Args:
            alpha: Input message
            secret_key: Secret key
            additional_data: Additional data for challenge
            salt: Optional salt for encoding
            
        Returns:
            Tuple[Point, Tuple[int, int]]: (output_point, (challenge, response))
        """
        raise NotImplementedError("Must be implemented by the VRF implementation")
    
    @abstractmethod
    def verify(
        self,
        *args
    ) -> bool:
        """
        Verify VRF proof.
        
        Args:
            public_key: Public key point
            input_point: Input point
            additional_data: Additional data used in proof
            output_point: Claimed output point
            proof: Proof tuple (challenge, response)
            
        Returns:
            bool: True if proof is valid
        """
        raise NotImplementedError("Must be implemented by the VRF implementation")