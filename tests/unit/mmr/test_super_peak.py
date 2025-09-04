from jam.utils.merkle import MMRFunctions
from tsrkit_types import Null, TypedVector
from jam.types.protocol.crypto import OpaqueHash, Hash
from jam.types.protocol.merkle import MMR, OptionHash


def test_super_peak():
    EXPECTED = OpaqueHash.fromhex(
        "f5df0c11416d43c55b43e096572d450b7780ed0fd7b540f26c8ded8e0d41e183"
    )
    DATA = MMR(
        [
            OptionHash(
                OpaqueHash.fromhex(
                    "4c31a1024d553c6f5eb90a26f9c53507d6d58b7be1197c0f86054b084353de5f"
                )
            ),
            OptionHash(Null),
            OptionHash(
                OpaqueHash.fromhex(
                    "7f64e54f8be039cea06582eb38e7f36f924c1f59a0f3043b4df6f140cccd6ddf"
                )
            ),
            OptionHash(
                OpaqueHash.fromhex(
                    "d7cc7a7751048dbe8d0232b5d0273acd874e56c19e41a2e09b590ca00e59908d"
                )
            ),
        ]
    )

    ACTUAL = MMRFunctions().super_peak(DATA)
    assert ACTUAL == EXPECTED


def test_beefy():
    fn = MMRFunctions()
    root = OpaqueHash.fromhex("f5df0c11416d43c55b43e096572d450b7780ed0fd7b540f26c8ded8e0d41e183")
    mmr = MMR(
        TypedVector[OptionHash](
            [
                OptionHash(
                    OpaqueHash.fromhex(
                        "4c31a1024d553c6f5eb90a26f9c53507d6d58b7be1197c0f86054b084353de5f"
                    )
                ),
                OptionHash(Null),
                OptionHash(
                    OpaqueHash.fromhex(
                        "7f64e54f8be039cea06582eb38e7f36f924c1f59a0f3043b4df6f140cccd6ddf"
                    )
                ),
                OptionHash(
                    OpaqueHash.fromhex(
                        "d7cc7a7751048dbe8d0232b5d0273acd874e56c19e41a2e09b590ca00e59908d"
                    )
                ),
            ]
        )
    )
    new_root = fn.super_peak(mmr)
    beefy = Hash.keccak256(fn.encode_mmr(mmr))
    assert root == new_root
