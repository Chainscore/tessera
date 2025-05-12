from jam.types.work.report import SingleShardKeysVector, SegmentsShard
from jam.work_package.package_db import ErasureShardsKeysMap, SegmentShardMap, BundleShardMap
from tests.dummy.utils import create_dummy_bytes32, create_dummy_bytes12, create_dummy_bytes
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base.integers.fixed import U16

def test_shard_db():
    """testing all three dbs that are storing shards"""
    # inserting data in Erasure root -> Shard keys Map DB
    print("starting")
    keys_db = ErasureShardsKeysMap()
    erasure_root = create_dummy_bytes32()
    ssr= create_dummy_bytes32()
    ssrs = [ssr]
    bh = create_dummy_bytes32()
    bhs = [bh]
    keys_db.put(erasure_root=erasure_root, segments_shard_roots=ssrs, bundles_hashes=bhs)
    data = keys_db.get_shards_keys(erasure_root=erasure_root)

    # inserting data in Segment Shard storage db
    sg_shard_db = SegmentShardMap()
    ssr_value = SegmentsShard([create_dummy_bytes12()])
    sg_shard_db.put(segments_shard_root=ssr, segments_shard=ssr_value)
    sg_shard_db.close()

    # inserting data in Bundle Shard storage db
    bd_shard_db = BundleShardMap()
    bh_value = Bytes(create_dummy_bytes(40))
    bd_shard_db.put(bundle_hash=bh, bundle_shard=bh_value)
    bd_shard_db.close()

    # fetching segment shard with erasure root and shard index
    segs_shard = keys_db.get_segments_shard(erasure_root=erasure_root, shard_index=U16(0))

    # fetching bundle shard with erasure root and shard index
    bd_shard = keys_db.get_bundle_shard(erasure_root=erasure_root, shard_index=U16(0))

    # finally closing Erasure root -> Shard keys Map DB
    keys_db.close()

    assert ssr == data[0].segment_shard_root
    assert bh == data[0].bundle_shard_hash
    assert ssr_value == segs_shard
    assert bh_value == bd_shard


