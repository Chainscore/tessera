"""Fuzzer target package for JAM conformance testing.

This package contains a tiny, well-structured API for running the JAM
fuzzer target. Implementation details live in submodules so tests and
consumers can import small, well-documented symbols from here.
"""

from .constants import *
from .types import *

__all__ = []
# Fuzzer target functionality for JAM conformance testing
