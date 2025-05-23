from jam.config.logging import logger
from jam.config.settings import settings
from jam.storage.item_extrinsics import ItemExtrinsics
from jam.types.base import Bytes

from jam.types.base.integers import U16
from jam.types.base.sequences.vector import Vector
from jam.types.extrinsics.extrinsic import Extrinsic

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
from jam.types.work.refine_context import OpaqueHashes

from jam.types.work.report import SegmentRootLookup, WorkPackageBundle



from jam.types.protocol.core import SegmentRoot
from jam.types.protocol.crypto import OpaqueHash

from jam.merklization.binary_merkle import BMRFunctions
from jam.utils.benchmark import benchmark

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
        # Access DA
        d3l = settings.d3l

        map_da = PackageSegmentMap(d3l)
        sr_lookup = SegmentRootLookup({})

        for item in p.items:
            for spec in item.import_segments:
                h = spec.tree_root
                n = spec.index
                try:
                    s_root = map_da.get(h)
                    if s_root and len(sr_lookup) < 8:
                        sr_lookup[h] = s_root
                except KeyError as e:
                    logger.warn(f"Either h is not package hash or {e}")

        self.sr_lookup = sr_lookup
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
        if self.sr_lookup.value is not None and r in self.sr_lookup.keys():
            return self.sr_lookup[r]
        else:
            return r

    @staticmethod
    def fetch_extrinsics(w: WorkItem, data: Extrinsic) -> Extrinsics:
        """
        Function X defined in Eqn 14.14
        Takes Work Item & retrieves its required extrinsic data

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1bcb011bd501?v=0.6.4
        Args:
           w: WorkItem
           data: bytes
        Returns:
           Extrinsic data (Vector[Bytes])
        """
        ext_da = ItemExtrinsics()
        ext: Extrinsics = ext_da.process_item(w, data)

        return ext


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

        # Access DA
        d3l = settings.d3l

        imports: Segments = Segments([])

        seg_da = SegmentsDA(d3l)
        sr_er_da = SegmentErasureMap(d3l)
        er_shards_da = ErasureShardsMap(d3l)

        # TODO: Use shards DA for reconstruction of segments
        # shards_da = SegmentShardsDA(d3l)

        seg_dict = SegmentDict({})

        for spec in w.import_segments:
            h = spec.tree_root
            n = spec.index

            s_root = self.lookup_root(h)
            logger.info(f"Fetching segments with root {s_root}")

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

        for spec in w.import_segments:
            r = spec.tree_root
            n = spec.index

            s_root = self.lookup_root(r)
            logger.info(f"Compiling justification for root {s_root}")

            if s_root not in seg_dict:
                raise KeyError("Segments not found")

            segments = seg_dict[s_root]
            pages = self.merkle.merkle_path_fn(segments, 0, int(n))
            justification = Justification(length=U16(len(pages)), justification=OpaqueHashes(pages))

            justifications.append(justification)

        return justifications

    def build_bundle(self, p: WorkPackage, x: Extrinsics) -> WorkPackageBundle:
        """Function to build Work Package Bundle"""

        all_imp = MultiSegments([])
        all_jfn = MultiJustifications([])
        all_ext = MultiExtrinsics([])

        for j, item in enumerate(p.items):
            # Fetch Imports
            with benchmark("Fetched imports"):
                imports = self.fetch_imports(item)
            all_imp.append(imports)

            # Fetch Justifications
            with benchmark("Compiling justifications"):
                justifications = self.fetch_justifications(item, j)
            all_jfn.append(justifications)

            # Fetch Extrinsics
            with benchmark("Processing extrinsics"):
                if len(x) > j:
                    extrinsics = self.fetch_extrinsics(item, x[j])
                    all_ext.append(extrinsics)

        bundle = WorkPackageBundle(p, all_ext, all_imp, all_jfn)

        logger.info("Compiling bundle..")
        return bundle