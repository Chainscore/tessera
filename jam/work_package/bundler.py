from jam.config.logging import logger
from jam.config.settings import settings
from jam.storage.db.kv import KVStore
from jam.types.base.sequences.vector import Vector

from jam.types.base.integers.general import Int

from jam.types.work.item import WorkItem
from jam.types.work.package import  WorkPackage
from jam.types.work.manifest import (
    Segments,
    MultiSegments,
    Justifications,
    Justification,
    Extrinsics,
    SegmentDict,
    MultiJustifications,
    MultiExtrinsics,
)

from jam.types.work.report import SegmentRootLookup, WorkPackageBundle



from jam.types.protocol.core import SegmentRoot
from jam.types.protocol.crypto import OpaqueHash

from jam.merklization.binary_merkle import BMRFunctions


from jam.work_package.stores.mappings import PackageSegmentMap, SegmentErasureMap, ErasureShardsMap
from jam.work_package.stores.segments import SegmentsDA

class Bundler:
    merkle: BMRFunctions
    sr_lookup: SegmentRootLookup
    segments_lookup: Vector[SegmentDict]

    def __init__(self):
        self.merkle = BMRFunctions()
        self.sr_lookup = SegmentRootLookup({})
        self.segments_lookup = Vector([])

    def build_lookup(self, p: WorkPackage) -> SegmentRootLookup:
        d3l = KVStore(settings.D3L_PATH)

        map_da = PackageSegmentMap(d3l)
        sr_lookup = SegmentRootLookup({})

        for item in p.items:
            for (h, n) in item.import_segments:
                s_root = map_da.get(h)
                if s_root and len(sr_lookup) < 8:
                    sr_lookup[h] = s_root

        self.sr_lookup = SegmentRootLookup
        d3l.close()
        return sr_lookup

    def lookup_root(self, r: OpaqueHash) -> SegmentRoot:
        """
        Segment root lookup function L defined in Eqn 14.12
        Collapses a union of segment-roots and work-package hashes into segment-roots using lookup dictionary

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1b7c011b9c01?v=0.6.4
        Args:
            r: OpaqueHash
        Returns:
            r if r is already a segment root else Segment root from dictionary if r is a work package hash.
        """
        if r in self.sr_lookup:
            return self.sr_lookup[r]
        else:
            return r

    @staticmethod
    def fetch_extrinsics(w: WorkItem) -> Extrinsics:
        """
        Function X defined in Eqn 14.14
        Takes Work Item & retrieves its required extrinsic data

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1bcb011bd501?v=0.6.4
        Args:
           w: WorkItem
        Returns:
           Extrinsic data (Vector[Bytes])
        """
        data: Extrinsics = Extrinsics([])

        # TODO: Fetch extrinsic from db / some pre-sent data whose hash and length are present in w.extrinsic
        # Extrinsic Store Ready (Integration Remaining)

        return data

    def fetch_imports(self, w: WorkItem) -> Segments:
        """
        Function S defined in Eqn 14.14
        Takes Work Item & retrieves required import segments

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1be0011bea01?v=0.6.4
        Args:
            w: WorkItem
        Returns:
            Import Segments (Vector[Segment])
        """

        imports: Segments = Segments([])
        d3l = KVStore(settings.D3L_PATH)

        seg_da = SegmentsDA(d3l)
        sr_er_da = SegmentErasureMap(d3l)
        er_shards_da = ErasureShardsMap(d3l)

        # TODO: Use shards DA for reconstruction of segments
        # shards_da = SegmentShardsDA(d3l)

        seg_dict = SegmentDict({})

        for (h, n) in w.import_segments:
            s_root = self.lookup_root(h)

            try:
                # Fetch segments directly from db first
                if s_root in seg_dict:
                    segments = seg_dict[s_root]
                    imports.append(segments[n])
                else:
                    segments, _ = seg_da.get(s_root)
                    seg_dict[s_root] = segments
                    imports.append(segments[n])

            except KeyError as e:
                logger.warn(f"Warning! {e}")
                logger.warn("Looking for segment shards in DA!")
                try:
                    e_root = sr_er_da.get(s_root)
                    shard_roots = er_shards_da.get_ss_roots(e_root)

                    if len(shard_roots) > 342:
                        # TODO: Reconstruct Shards
                        ...
                    else:
                        # TODO: Fetch Missing Shards
                        ...

                except KeyError as e2:
                    logger.warn(f"Warning! {e2}")
                    logger.warn("Fetching all segment shards from assurers!")

                    # TODO: Fetch All Shards

        self.segments_lookup.append(seg_dict)
        d3l.close()

        return imports

    def fetch_justifications(self, w: WorkItem, i: int) -> Justifications:
        """
        Function J defined in Eqn 14.14
        Takes work item and compiles justifications of import segments data

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1bf0011bfe01?v=0.6.4
        Args:
            w: Work Item
            i: Item Index
        Returns:
            Length prefixed justification
        """

        justifications: Justifications = Justifications([])
        seg_dict = self.segments_lookup[i]

        for (r, n) in w.import_segments:
            s_root = self.lookup_root(r)

            segments = seg_dict[s_root]
            pages = self.merkle.merkle_path_fn(segments, 0, int(n))
            justification = Justification(Int(len(pages)), pages)

            justifications.append(justification)

        return justifications

    def build_bundle(self, p: WorkPackage) -> WorkPackageBundle:
        """Function to build Work Package Bundle"""

        all_imp = MultiSegments([])
        all_jfn = MultiJustifications([])
        all_ext = MultiExtrinsics([])

        for j, item in enumerate(p.items):
            # Fetch Imports
            imports = self.fetch_imports(item)
            all_imp.append(imports)

            # Fetch Justifications
            justifications = self.fetch_justifications(item, j)
            all_jfn.append(justifications)

            # Fetch Extrinsics
            extrinsics = self.fetch_extrinsics(item)
            all_ext.append(extrinsics)

        bundle = WorkPackageBundle(p, all_ext, all_imp, all_jfn)

        return bundle