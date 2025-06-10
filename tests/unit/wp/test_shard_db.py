from rockstore import RockStore
from tsrkit_types import Bytes

from jam.types.work.shard import SegmentsShard, SegmentsShardRoots, BundleShardHashes, SegmentsShardUnit, ShardIndex, \
    BundleShardUnit
from jam.utils.dummy.utils import create_dummy_bytes32, create_dummy_bytes12, create_dummy_bytes
from jam.work_package.stores.audits import AuditShardsDA
from jam.work_package.stores.mappings import ErasureShardsMap
from jam.work_package.stores.segments import SegmentShardsDA

def test_shard_db(db_path):
    """testing all three dbs that are storing shards"""
    # inserting data in Erasure root -> Shard keys Map DB
    db = RockStore(db_path)

    keys_db = ErasureShardsMap(db)
    erasure_root = create_dummy_bytes32()
    ssr_list = [create_dummy_bytes32() for _ in range(1023)]
    bh_list = [create_dummy_bytes32() for _ in range(1023)]
    ssrs = SegmentsShardRoots(ssr_list)
    bhs = BundleShardHashes(bh_list)


    keys_db.put_batch(root=erasure_root, ss_roots=ssrs, bs_hashes=bhs)
    data = keys_db.get(root=erasure_root)

    # inserting data in Segment Shard storage db
    sg_shard_db = SegmentShardsDA(db)
    seg_shard = SegmentsShard([create_dummy_bytes12()])
    for i, ssr in enumerate(ssr_list):
        ssr_value = SegmentsShardUnit(shard_index=ShardIndex(i), shard=seg_shard)
        sg_shard_db.put(root=ssr, data=ssr_value)


    # inserting data in Bundle Shard storage db
    bd_shard_db = AuditShardsDA(db)
    bundle_shard = Bytes(create_dummy_bytes(40))
    for i, bh in enumerate(bh_list):
        bh_value = BundleShardUnit(shard_index=ShardIndex(i), shard=bundle_shard)
        bd_shard_db.put(bs_hash=bh, data=bh_value)

    # validation of 10 shards
    for i in range(1):
        shard_index = ShardIndex(i)

        # Segment shard retrieval and check
        segs_shard_root = keys_db.get_ss_root(root=erasure_root, shard_index=shard_index)
        if segs_shard_root:
            segs_shard = sg_shard_db.get(segs_shard_root.segment_shard_root)
            assert segs_shard_root.segment_shard_root == ssr_list[i]
            assert segs_shard == (seg_shard, i)

        # Bundle shard retrieval and check
        bd_shard_hash = keys_db.get_bs_hash(root=erasure_root, shard_index=shard_index)
        bd_shard = bd_shard_db.get(bs_hash=bd_shard_hash.bundle_shard_hash)
        assert bd_shard_hash.bundle_shard_hash == bh_list[i]
        assert bd_shard == (bundle_shard, i)

    db.close()


