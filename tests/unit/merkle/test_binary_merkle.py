from tsrkit_types import TypedVector, Bytes

from jam.types import ErasureRoot
from jam.types.work.shard import BundleShardHashes, SegmentsShardRoots, ShardKey
from jam.utils.merkle import BMRFunctions

bs_hashes = BundleShardHashes.from_json([
      "0x4a9f62476ba6cd6f36937f9eebf09c72fdf45819462c468e060e6b1530fb3e35",
      "0x55fa47ee83f55405127cbd47f02d08413f078cd812792ba0874ae8543c0717c7",
      "0x2acfff2bef63a34b8f7caf6115e4614df6ad8f72c8781698b2e0a55d4b740d47",
      "0x9e7d3680e15f54908ec85759427db3618da72c240d46fb3f45c6c9b7fbdfb378",
      "0x73ec904f29c724480b6591a26a9e68016029bdcab3fd3b9defeee308bd729d29",
      "0x8e057d8592553caef80a4231f2f513cdf17433a35beaa467f259dd57e8bb99f5"
    ])

ss_roots = SegmentsShardRoots.from_json([
      "0xdbede047e65f4ef346aeda8b96cb3cfdf55d4c68b177973c6e7cbf1eaa499a32",
      "0xbf51f6e47d680f32a00b909628c18cb1ea57a2a8c5eee503e7ec1bf1c18105a7",
      "0x895defb15c5d7a194eab3828388890c075552aa1b265c574e389cffc4a90bd85",
      "0x8fa50307940d19e0ef108fad500e94d72bbf68b9b944a5b91a906c9d2511d3ff",
      "0x811abce04c7c518d37ad931aa059257cc8ac1c5fd6aec3c317c012c2f4713d7b",
      "0xe6996fee88b15e45f0cb14b15c3ba5f187219a93227664f8a6ec0a6c9eceeb7c"
    ])

def test_wb_merklize():
    merklizer = BMRFunctions()

    shards_keys = TypedVector[Bytes]([])
    for i in range(6):
        shards_key = ShardKey(bs_hashes[i], ss_roots[i])
        shards_keys.append(Bytes(shards_key.encode()))

    expected_root = ErasureRoot.fromhex("5ee7176f1393ae41269cc4f6f78bbc5287a0858e1069f29903c33415f87f9579")
    root = merklizer.wb_merklize(shards_keys)

    print("\nGOT ROOT", root.hex(), root==expected_root)
    assert  root == expected_root