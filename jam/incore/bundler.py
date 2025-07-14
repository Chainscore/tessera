from typing import Tuple, Dict, List

from tsrkit_types.sequences import Vector

from jam.logging import get_logger
from jam.network.node import Node

from jam.storage.da.mappings import PackageSegmentMap, SegmentErasureMap
from jam.storage.da.segments import SegmentsDA, SegmentShardsDA
from jam.storage.item_extrinsics import ItemExtrinsics

from jam.types.protocol.core import SegmentRoot
from jam.types.protocol.crypto import OpaqueHash

from jam.types.work.item import WorkItem
from jam.types.work.manifest import (
    Segments,
    SegmentIndex,
    MultiSegments,
    Justifications,
    Justification,
    Extrinsics,
    SegmentDict,
    MultiJustifications,
    MultiExtrinsics,
    Extrinsic,
    Segment,
    SegmentRootLookup
)
from jam.types.work.package import WorkPackage, WorkPackageBundle
from jam.types.work.shard import ShardIndex, SegmentShard

from jam.utils.benchmark import benchmark
from jam.utils.merkle import BMRFunctions
from jam.utils.erasure_coding.erasure_code import ErasureCode
from jam.utils.chainspec import chain_config


# Module-specific logger
logger = get_logger("in_core")


class Bundler:
    merkle: BMRFunctions
    sr_lookup: SegmentRootLookup
    segments_lookup: Vector[SegmentDict]
    node: Node

    def __init__(self, node: Node):
        self.merkle = BMRFunctions()
        self.sr_lookup = SegmentRootLookup({})
        self.segments_lookup = Vector([])
        self.node = node

    def build_lookup(self, p: WorkPackage) -> SegmentRootLookup:
        # Access DA
        from jam.settings import settings

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
        if self.sr_lookup is not None and r in self.sr_lookup.keys():
            logger.debug("Lookup Hit")
            return self.sr_lookup[r]
        else:
            logger.debug("Lookup Miss")
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
        # Access DA
        from jam.settings import settings

        db = settings.main_db

        ext_da = ItemExtrinsics(db)
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
        from jam.settings import settings

        d3l = settings.d3l

        imports: Segments = Segments([])

        seg_da = SegmentsDA(d3l)
        sr_er_da = SegmentErasureMap(d3l)
        shards_da = SegmentShardsDA(d3l)

        erasure_code = ErasureCode()

        # Cached Segments
        seg_dict = SegmentDict({})

        shards_dict: Dict[SegmentRoot, List[Tuple[ShardIndex, List[SegmentShard]]]] = {}

        # Pre-computed map for imports
        import_map: Dict[OpaqueHash, List[SegmentIndex]] = {}
        for spec in w.import_segments:
            h = spec.tree_root
            n = spec.index

            if h in import_map:
                import_map[h].append(n)
            else:
                import_map[h] = [n]

        fetched_imports: Dict[Tuple[SegmentRoot, SegmentIndex], Segment] = {}
        # requested_shards: Dict[Tuple[SegmentRoot,SegmentIndex], Dict[ShardIndex, Tuple[Assurers, ErasureRoot]]] = {}

        for h, seg_indices in import_map.items():
            s_root = self.lookup_root(h)
            logger.info(f"Fetching segments with root {s_root}")

            for n in seg_indices:
                try:
                    # Check for Segments in cache first
                    if s_root in seg_dict:
                        logger.debug("Cache Hit")
                        segments = seg_dict[s_root]
                        fetched_imports[(s_root, n)] = segments[n]

                    # If cache miss, check in DB, and cache it
                    else:
                        logger.debug("Cache Miss")
                        segments, _ = seg_da.get(s_root)
                        logger.debug("Fetching segments from root", segment_root=s_root.hex())
                        seg_dict[s_root] = segments
                        logger.debug(
                            "Fetched segments from root",
                            segment_root=s_root.hex(),
                            count=len(segments),
                        )
                        fetched_imports[(s_root, n)] = segments[n]

                except KeyError as e:
                    logger.warn(f"Warning! {e}")
                    logger.warn("Looking for segment shards in DA!")

                    # Get Erasure Root
                    e_root = sr_er_da.get(s_root)
                    try:
                        # CASE: Not enough shards available
                        # CASE: Enough shards available
                        # CASE: Not enough segment indexed Shards
                        # CASE: Enough Segment indexed Shards
                        # TOTAL POSSIBILITIES IV

                        # FOR NOW JUST REQUEST ALL THE SHARDS (SOMEWHAT GREATER THAN 341)
                        # TODO: Fetch shards based on self availability

                        logger.debug("Segment Miss")
                        ss_dict = shards_da.get(e_root)
                        shards = ss_dict.get_shard_tuple(n)
                        if len(shards) > chain_config.recovery_threshold:
                            segment = Segment(erasure_code.decode(shards))
                            fetched_imports[(s_root, n)] = segment

                        else:
                            raise KeyError("Not enough shards available")

                    except KeyError as e2:
                        logger.debug("Shard Miss")

                        # TODO: Request all shards using CE 137
                        from jam.network.protocols.ce_137 import ShardDistributionProtocol
                        ce_137 = ShardDistributionProtocol()

                        # TODO: Reconstruct Segment
                        # BLOCKER: Fetching is asynchronous, need to handle that properly.
                        logger.error(f"Unable to import segment {n} of seg root {s_root}")
                        raise NotImplementedError("Shard Requesting isn't integrated")
                except Exception as e:
                    logger.error(f"Exception occurred fetching imports ({s_root},{n})")

        for spec in w.import_segments:
            h = spec.tree_root
            n = spec.index
            segment = fetched_imports[(h, n)]
            imports.append(segment)

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
            try:
                r = spec.tree_root
                n = spec.index

                s_root = self.lookup_root(r)
                logger.info(f"Compiling justification for root {s_root}")

                if s_root not in seg_dict:
                    raise KeyError("Segments not found")

                segments = seg_dict[s_root]
                pages = self.merkle.merkle_path_fn(segments, 0, int(n))
                justification = Justification(pages.unwrap())

                justifications.append(justification)
            except Exception as e:
                logger.error(f"Unable to compile justification for item {i+1}")

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
