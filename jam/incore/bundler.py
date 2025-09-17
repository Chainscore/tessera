import asyncio
from math import ceil
from typing import Tuple, Dict, List, Set

from tsrkit_types.sequences import Vector
from tsrkit_types.integers import Uint
from tsrkit_types.bytes import Bytes

from jam.incore.error import BundlerError, BundlerErrorCode as Code
from jam.incore.utils import Utils

from jam.log_setup import pvm_logger as logger

from jam.network.node import Node
from jam.network.utils.shards import get_vi
from jam.network.protocols.ce_139_base import SegmentIndexes, Query, Queries, CE139Data

from jam.storage.da.reports import ReportsDA
from jam.storage.da.mappings import PackageSegmentMap, SegmentErasureMap, ErasureAssurerMap
from jam.storage.da.segments import SegmentsDA, SegmentShardsDA
from jam.storage.item_extrinsics import ItemExtrinsics

from jam.types.work.item import WorkItem, TreeRoot
from jam.types.work.package import WorkPackage, WorkPackageBundle
from jam.types.work.report import WorkReport
from jam.types.work.shard import ShardIndex, SegmentShard
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
    Segment,
    SegmentRootLookup
)

from jam.types.protocol.core import SegmentRoot
from jam.types.protocol.crypto import OpaqueHash

from jam.utils.chainspec import chain_config
from jam.utils.gather import gather_with_exceptions
from jam.utils.merkle.binary_merkle import BMRFunctions, OpaqueHashes
from jam.utils.erasure_coding.erasure_code import ErasureCode


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
        from jam.settings import settings

        d3l = settings.d3l

        map_da = PackageSegmentMap(d3l)
        sr_lookup = SegmentRootLookup({})

        for item in p.items:
            for spec in item.import_segments:
                h = spec.tree_root
                n = spec.index

                if isinstance(h, SegmentRoot):
                    continue

                try:
                    s_root = map_da.get(h)
                    if s_root and len(sr_lookup) < 8:
                        sr_lookup[h] = s_root
                except KeyError as e:
                    logger.warn(
                        f"Work Package Hash not known.",
                        err=str(e),
                    )

        self.sr_lookup = sr_lookup
        return sr_lookup

    def lookup_root(self, r: TreeRoot) -> SegmentRoot:
        """
        Segment root lookup function L defined in Eqn 14.13
        Collapses a union of segment-roots and work-package hashes into segment-roots using lookup dictionary

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1c1a001c3700?v=0.7.0
        Args:
            r: TreeRoot
        Returns:
            r, if r is already a segment root, else Segment root from dictionary if r is a work package hash.
        """
        if isinstance(r, SegmentRoot):
            logger.debug("Lookup Skip", sr_root=r.hex()[:16] + "...")
            return r
        else:
            if self.sr_lookup is not None and r in self.sr_lookup.keys():
                logger.debug("Lookup Hit", wp_hash=r.hex()[:16] + "...")
                return SegmentRoot(self.sr_lookup[r])
            else:
                logger.error(
                    f"Exception occurred fetching root from lookup",
                    wp_hash=r.hex(),
                )
                raise BundlerError(Code.LOOKUP_ERROR)

    @staticmethod
    def fetch_extrinsics(w: WorkItem, data: Bytes) -> Extrinsics:
        """
        Function X defined in Eqn 14.15
        Takes Work Item & retrieves its required extrinsic data

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1c77001c8e00?v=0.7.0
        Args:
           w: WorkItem
           data: Bytes
        Returns:
           Extrinsic data (Vector[Bytes])
        """

        # Access DA
        from jam.settings import settings

        db = settings.main_db

        ext_da = ItemExtrinsics(db)
        ext: Extrinsics = ext_da.process_item(w, data)

        return ext

    async def fetch_imports(self, w: WorkItem):
        """
        Function S defined in Eqn 14.15
        Takes Work Item & retrieves required import segments

        Notes:
            - First we precompute required import indices for a work item for a specific root
            - After precomputations, we maintain a cache of fetched segment for each seg root and index
            - If segment is not available in our db, we check for its shards
            - If shards are also not available, we request specific validators who have those particular shards
            - We fetch shards for all the required indices in a single transmit call per shard.
            - Once shards are fetched, they are then used to reconstruct segments.
            - Constructed / Fetched segments are then stored in a map w.r.t seg root amd seg index (to import)
            - Import Segments are then compiled and returned
            - In case of error, Bundle Error is raised
        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1c99001cb400?v=0.7.0
        Args:
            w: Work Item
        Returns:
            Import Segments (Vector[Segment]) for given work item
        Raises:
            Bundler Error: If Segments aren't computed due to any reason (which can be traced back)
        """

        imports: Segments = Segments([])

        # Access DA
        from jam.settings import settings

        d3l = settings.d3l

        seg_da = SegmentsDA(d3l)
        sr_er_da = SegmentErasureMap(d3l)
        shards_da = SegmentShardsDA(d3l)
        er_ar_da = ErasureAssurerMap(d3l)
        wr_da = ReportsDA(d3l)

        erasure_code = ErasureCode()

        subtree_depth = 6
        subtree_page_size = 2**subtree_depth

        # Pre-computed map for imports
        # Segment Root -> ([(Segment Index to import, Its Relative proof page)], Its OG Work Report)
        import_map: Dict[SegmentRoot, Tuple[List[SegmentIndex], WorkReport]] = {}

        for spec in w.import_segments:
            h = spec.tree_root
            n = spec.index

            r = self.lookup_root(h)
            if r in import_map:
                import_map[r][0].append(n)

            else:
                e_root = sr_er_da.get(r)
                wr_hash, _ = er_ar_da.get(e_root)
                wr = wr_da.get(wr_hash)

                import_map[r] = ([n], wr)

        # Fetched Segs
        fetched_imports: Dict[Tuple[SegmentRoot, SegmentIndex], Segment] = {}

        for s_root in import_map:
            metadata = import_map[s_root]

            wr = metadata[1]
            e_root = wr.package_spec.erasure_root
            seg_indices = metadata[0]

            logger.info(
                f"Fetching segments..",
                seg_root=s_root.hex(),
                er_root=e_root.hex(),
                indices=seg_indices,
            )

            exports_count = wr.package_spec.exports_count
            total_proofs = ceil(exports_count / subtree_page_size)
            total_count = exports_count + total_proofs

            # ------------------------
            # Cached Segments & Shards
            # ------------------------

            # {Segment Index -> Proof}
            segs_dict: Dict[SegmentIndex, Segment] = {}

            # {Segment Index -> [SegmentShard, ShardIndex]}
            shards_dict: Dict[SegmentIndex, List[Tuple[SegmentShard, ShardIndex]]] = {}

            # ------------------------

            # Segment Indices
            # TODO: Is sorting important here? To be thought upon.
            ind_to_req = SegmentIndexes(sorted(seg_indices))

            for n in seg_indices:
                try:
                    # Check for Segments in Cached Segments first
                    if n in segs_dict:
                        logger.debug(
                            "Segments Cache Hit",
                            seg_root=s_root.hex()[:16],
                            er_root=e_root.hex()[:16],
                            seg_ind=n,
                        )
                        fetched_imports[(s_root, n)] = segs_dict[n]

                    # If cache miss, check in DB, and cache it
                    else:
                        logger.debug(
                            "Segments Cache Miss",
                            seg_root=s_root.hex()[:16],
                            er_root=e_root.hex()[:16],
                            seg_ind=n,
                        )
                        logger.info(
                            "Fetching segments from root", segment_root=s_root.hex()
                        )
                        segments, _ = seg_da.get(s_root)

                        for i, segment in enumerate(segments):
                            segs_dict[i] = segment

                        logger.debug(
                            "Fetched segments from root",
                            segment_root=s_root.hex(),
                            count=len(segments),
                        )
                        fetched_imports[(s_root, n)] = segments[n]

                except KeyError as SEG_MISS:
                    logger.warning(
                        "Looking for segment shards in DA!",
                        err=str(SEG_MISS),
                        err_type=type(SEG_MISS).__name__,
                    )

                    try:
                        logger.debug(
                            "Segment Miss",
                            seg_root=s_root.hex()[:16],
                            er_root=e_root.hex()[:16],
                            seg_ind=n,
                        )

                        # No need to check for shards in Cache as we
                        # already would have built segment and stored in segment cache.

                        # Check for Segment Shards in DB
                        ss_dict = shards_da.get(e_root)

                        # We must have at least one shard in DB
                        if not ss_dict or len(ss_dict) == 0:
                            logger.debug(
                                "Unrecognised Erasure root found!",
                                er_root=e_root.hex()[:16],
                            )
                            raise KeyError(
                                "Unrecognised Erasure root found. No segment shards available."
                            )

                        # Fetch total length of segments formed (including proofs)
                        s_dicts = list(ss_dict.values())
                        total_segments = len(s_dicts[0])

                        if total_segments <= n:
                            raise IndexError(
                                f"Total segments known for this er-root are {total_segments}, must be {total_count}"
                            )

                        if len(ss_dict) < chain_config.recovery_threshold:
                            logger.debug(
                                "Shards in database are less than recovery threshold",
                                er_root=e_root.hex()[:16],
                                shards=len(ss_dict),
                            )
                            raise KeyError(
                                "Not enough segment shards available in database!"
                            )

                        for i in ind_to_req:
                            shards = ss_dict.get_shard_tuple(i)

                            if len(shards) >= chain_config.recovery_threshold:
                                segment = Segment(erasure_code.decode(Vector(shards)))
                                segs_dict[i] = segment
                            else:
                                logger.debug(
                                    "Shards in database are less than recovery threshold",
                                    er_root=e_root.hex()[:16],
                                    shards=len(ss_dict),
                                    shard_ind=i,
                                )
                                raise KeyError(
                                    f"Not enough shards available in database for segment {i}"
                                )

                        fetched_imports[(s_root, n)] = segs_dict[n]

                    except KeyError as SHARD_MISS:
                        logger.debug(
                            "Segment Shard Miss",
                            err=str(SHARD_MISS),
                            err_type=type(SHARD_MISS).__name__,
                            seg_root=s_root.hex()[:16],
                            er_root=e_root.hex()[:16],
                            seg_ind=n,
                        )

                        from jam.network.protocols import SegmentShardRequest

                        ce_139 = SegmentShardRequest()
                        for i in range(chain_config.num_validators):
                            vi = get_vi(i, wr.core_index)

                            query = Query(e_root, ShardIndex(i), ind_to_req)
                            queries = Queries([query])
                            length = Uint[32](len(queries.encode()))
                            ce_139_data = CE139Data(length, queries)

                            if self.node.validator_index != vi:
                                data = await ce_139.transmit(self.node, ce_139_data)
                                if (
                                    data
                                    and len(data) == 1
                                    and data[0]
                                    and len(data[0]) == len(ind_to_req)
                                ):
                                    responses = data[0]

                                    for s, s_i in zip(responses, ind_to_req):
                                        if s and isinstance(s, SegmentShard):
                                            if s_i in shards_dict:
                                                shards_dict[s_i].append(
                                                    (s, ShardIndex(i))
                                                )
                                            else:
                                                shards_dict[s_i] = [(s, ShardIndex(i))]

                        for i in ind_to_req:
                            shards = shards_dict[i]

                            if len(shards) > chain_config.recovery_threshold:
                                segment = Segment(erasure_code.decode(Vector(shards)))
                                segs_dict[i] = segment
                            else:
                                logger.debug(
                                    "Fetched Shards are less than recovery threshold",
                                    er_root=e_root.hex()[:16],
                                    shards=len(shards),
                                    shard_ind=i,
                                )
                                raise KeyError(
                                    f"Not enough shards fetched for segment {i}"
                                )

                        fetched_imports[(s_root, n)] = segs_dict[n]

                except Exception as SEGMENT_MISS:
                    logger.error(
                        f"Exception occurred fetching segments ({s_root},{n})",
                        err=str(SEGMENT_MISS),
                        err_type=type(SEGMENT_MISS).__name__,
                    )
                    raise BundlerError(Code.SEG_ERROR)

        for spec in w.import_segments:
            h = spec.tree_root
            n = spec.index
            if (h, n) not in fetched_imports:
                logger.error(
                    f"Exception occurred compiling segments ({h},{n})",
                )
                raise BundlerError(Code.SEG_ERROR)

            segment = fetched_imports[(h, n)]
            imports.append(segment)

        return imports

    async def fetch_justifications(self, w: WorkItem) -> Justifications:
        """
        Function J defined in Eqn 14.15
        Takes work item and compiles justifications of import segments data

        Notes:
            - First we precompute required import indices for a work item for a specific root
            - Then for each segment root, we calculate required proof segment index
            - After precomputations, we maintain a cache of fetched proofs for each seg root
            - If proof is not available in our db, we check for its shards
            - If shards are also not available, we request specific validators who have those particular shards
            - We fetch shards for all the required indices in a single transmit call per shard.
            - Once shards are fetched, they are then used to reconstruct proofs.
            - Constructed / Fetched proofs are then stored in a map w.r.t seg root amd seg index (to import)
            - Justifications are then compiled and returned
            - In case of error, Bundle Error is raised
        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1cba001cd600?v=0.7.0
        Args:
            w: Work Item
        Returns:
            Length prefixed justification
        Raises:
            Bundler Error: If Justifications aren't computed due to any reason (which can be traced back)
        """

        justifications: Justifications = Justifications([])

        # Access DA
        from jam.settings import settings

        d3l = settings.d3l

        seg_da = SegmentsDA(d3l)
        sr_er_da = SegmentErasureMap(d3l)
        shards_da = SegmentShardsDA(d3l)
        er_ar_da = ErasureAssurerMap(d3l)
        wr_da = ReportsDA(d3l)

        erasure_code = ErasureCode()
        utils = Utils()

        subtree_depth = 6
        subtree_page_size = 2**subtree_depth

        # Pre-computed map for imports
        # Segment Root -> ([(Segment Index to import, Its Relative proof page)], Its OG Work Report)
        import_map: Dict[
            SegmentRoot, Tuple[List[Tuple[SegmentIndex, SegmentIndex]], WorkReport]
        ] = {}

        # Pre-computed map for required proof pages
        req_index_map: Dict[SegmentRoot, Set[int]] = {}
        for spec in w.import_segments:
            h = spec.tree_root
            n = spec.index

            r = self.lookup_root(h)

            # Relative proof page index
            page_index = int(n // subtree_page_size)

            if r in import_map:
                _, wr = import_map[r]
                exp_cnt = wr.package_spec.exports_count

                req_index_map[r].add(exp_cnt + page_index)
                import_map[r][0].append((n, page_index))

            else:
                e_root = sr_er_da.get(r)
                wr_hash, _ = er_ar_da.get(e_root)
                wr = wr_da.get(wr_hash)
                exp_cnt = wr.package_spec.exports_count

                req_index_map[r] = set()
                req_index_map[r].add(exp_cnt + page_index)
                import_map[r] = ([(n, page_index)], wr)

        # Fetched Jfns
        fetched_jfns: Dict[Tuple[SegmentRoot, SegmentIndex], OpaqueHashes] = {}

        for s_root in import_map:
            metadata = import_map[s_root]

            wr = metadata[1]
            e_root = wr.package_spec.erasure_root
            proof_indices = metadata[0]

            logger.info(
                f"Fetching justifications..",
                seg_root=s_root.hex(),
                er_root=e_root.hex(),
                indices=proof_indices,
            )

            exports_count = wr.package_spec.exports_count
            total_proofs = ceil(exports_count / subtree_page_size)
            total_count = exports_count + total_proofs

            # ------------------------
            # Cached Proofs & Shards
            # ------------------------

            # {Relative Proof Page Index -> Proof}
            proofs_dict: Dict[SegmentIndex, Segment] = {}

            # {Actual Proof Page Index -> [ProofShard, ShardIndex]}
            shards_dict: Dict[SegmentIndex, List[Tuple[SegmentShard, ShardIndex]]] = {}

            # ------------------------

            # Actual Proof Page Indices
            ind_to_req = SegmentIndexes(sorted(list(req_index_map[s_root])))

            for n, p in proof_indices:
                try:
                    # Check for Pages in Cached Proofs first
                    if p in proofs_dict:
                        logger.debug(
                            "Proofs Cache Hit",
                            seg_root=s_root.hex()[:16],
                            er_root=e_root.hex()[:16],
                            seg_ind=n,
                            proof_ind=(exports_count + p),
                        )
                        proof = proofs_dict[p]

                        _, jfn = utils.zero_depth_proof(proof, n)
                        fetched_jfns[(s_root, n)] = jfn

                    # If cache miss, check in DB, and cache it
                    else:
                        logger.debug(
                            "Proofs Cache Miss",
                            seg_root=s_root.hex()[:16],
                            er_root=e_root.hex()[:16],
                            seg_ind=n,
                            proof_ind=(exports_count + p),
                        )
                        logger.info(
                            "Fetching proof segments from root",
                            segment_root=s_root.hex(),
                        )
                        _, proofs = seg_da.get(s_root)

                        for i, proof in enumerate(proofs):
                            proofs_dict[i] = proof

                        logger.debug(
                            "Fetched proof segments from root",
                            segment_root=s_root.hex(),
                            count=len(proofs),
                        )
                        _, jfn = utils.zero_depth_proof(proofs[p], n)

                        fetched_jfns[(s_root, n)] = jfn

                except KeyError as PROOF_MISS:
                    logger.warning(
                        "Looking for proof shards in DA!",
                        err=str(PROOF_MISS),
                        err_type=type(PROOF_MISS).__name__,
                    )

                    try:
                        logger.debug(
                            "Proof Miss",
                            seg_root=s_root.hex()[:16],
                            er_root=e_root.hex()[:16],
                            seg_ind=n,
                            proof_ind=(exports_count + p),
                        )

                        # No need to check for shards in Cache as we
                        # already would have built proof and stored in proof cache.

                        # Check for Pages Shards in DB
                        ss_dict = shards_da.get(e_root)

                        # We must have at least one shard in DB
                        if not ss_dict or len(ss_dict) == 0:
                            logger.debug(
                                "Unrecognised Erasure root found!",
                                er_root=e_root.hex()[:16],
                            )
                            raise KeyError(
                                "Unrecognised Erasure root found. No proof shards available."
                            )

                        # Fetch total length of segments formed (including proofs)
                        s_dicts = list(ss_dict.values())
                        total_segments = len(s_dicts[0])

                        if total_segments <= n:
                            raise IndexError(
                                f"Total segments known for this er-root are {total_segments}, must be {total_count}"
                            )

                        if len(ss_dict) < chain_config.recovery_threshold:
                            logger.debug(
                                "Shards in database are less than recovery threshold",
                                er_root=e_root.hex()[:16],
                                shards=len(ss_dict),
                            )
                            raise KeyError(
                                "Not enough proof shards available in database!"
                            )

                        for i in ind_to_req:
                            shards = ss_dict.get_shard_tuple(i)

                            if len(shards) >= chain_config.recovery_threshold:
                                proof = Segment(erasure_code.decode(Vector(shards)))
                                proofs_dict[i - exports_count] = proof
                            else:
                                logger.debug(
                                    "Shards in database are less than recovery threshold",
                                    er_root=e_root.hex()[:16],
                                    shards=len(ss_dict),
                                    shard_ind=i,
                                )
                                raise KeyError(
                                    f"Not enough shards available in database for proof segment {i}"
                                )

                        _, jfn = utils.zero_depth_proof(proofs_dict[p], n)
                        fetched_jfns[(s_root, n)] = jfn

                    except KeyError as SHARD_MISS:
                        logger.debug(
                            "Proof Shard Miss",
                            err=str(SHARD_MISS),
                            err_type=type(SHARD_MISS).__name__,
                            seg_root=s_root.hex()[:16],
                            er_root=e_root.hex()[:16],
                            seg_ind=n,
                            proof_ind=(exports_count + p),
                        )

                        from jam.network.protocols import SegmentShardRequest

                        ce_139 = SegmentShardRequest()
                        for i in range(chain_config.num_validators):
                            vi = get_vi(i, wr.core_index)

                            query = Query(e_root, ShardIndex(i), ind_to_req)
                            queries = Queries([query])
                            length = Uint[32](len(queries.encode()))
                            ce_139_data = CE139Data(length, queries)

                            if self.node.validator_index != vi:
                                data = await ce_139.transmit(self.node, ce_139_data)
                                if (
                                    data
                                    and len(data) == 1
                                    and data[0]
                                    and len(data[0]) == len(ind_to_req)
                                ):
                                    responses = data[0]

                                    for s, p_i in zip(responses, ind_to_req):
                                        if s and isinstance(s, SegmentShard):
                                            if p_i in shards_dict:
                                                shards_dict[p_i].append(
                                                    (s, ShardIndex(i))
                                                )
                                            else:
                                                shards_dict[p_i] = [(s, ShardIndex(i))]

                        for i in ind_to_req:
                            shards = shards_dict[i]

                            if len(shards) > chain_config.recovery_threshold:
                                proof = Segment(erasure_code.decode(Vector(shards)))
                                proofs_dict[i - exports_count] = proof
                            else:
                                logger.debug(
                                    "Fetched Shards are less than recovery threshold",
                                    er_root=e_root.hex()[:16],
                                    shards=len(shards),
                                    shard_ind=i,
                                )
                                raise KeyError(
                                    f"Not enough shards fetched for proof segment {i}"
                                )

                        _, jfn = utils.zero_depth_proof(proofs_dict[p], n)
                        fetched_jfns[(s_root, n)] = jfn

                except Exception as JFN_MISS:
                    logger.error(
                        f"Exception occurred fetching justifications ({s_root},{n})",
                        err=str(JFN_MISS),
                        err_type=type(JFN_MISS).__name__,
                    )
                    raise BundlerError(Code.JFN_ERROR)

        for spec in w.import_segments:
            try:
                r = spec.tree_root
                n = spec.index

                s_root = self.lookup_root(r)
                logger.debug(
                    f"Compiling justification.", s_root=s_root.hex()[:16], index=n
                )

                if (s_root, n) not in fetched_jfns:
                    raise KeyError(
                        f"Proofs not found for root: {s_root.hex()[:16]}, index: {n}"
                    )

                jfn = fetched_jfns[(s_root, n)]
                justification = Justification([])

                for node in jfn:
                    justification.append(Bytes(node))

                justifications.append(justification)
            except Exception as e:
                logger.error(
                    f"Unable to compile justification.",
                    err=e,
                    err_type=type(e).__name__,
                    item=w,
                    root=spec.tree_root,
                    index=spec.index,
                )

        return justifications

    async def build_bundle(self, p: WorkPackage, x: Extrinsics) -> WorkPackageBundle:
        """Function to build Work Package Bundle"""

        all_imp = MultiSegments([])
        all_jfn = MultiJustifications([])
        all_ext = MultiExtrinsics([])

        for j, item in enumerate(p.items):
            # Fetch Imports
            logger.debug("Fetching imports..", work_item=j)
            imports_task = asyncio.create_task(self.fetch_imports(item))

            # Fetch Justifications
            logger.debug("Compiling justifications..", work_item=j)
            justifications_task = asyncio.create_task(self.fetch_justifications(item))

            imports = await gather_with_exceptions([imports_task, justifications_task])
            # imports = await gather_with_exceptions([imports_task])

            all_imp.append(imports[0])
            all_jfn.append(imports[1])

            # Fetch Extrinsics
            logger.debug("Processing extrinsics..", work_item=j)
            if len(x) > j:
                extrinsics = self.fetch_extrinsics(item, x[j])
                all_ext.append(extrinsics)
            else:
                logger.error(
                    "Invalid extrinsics length",
                    expected_len=len(p.items),
                    got_len=len(x),
                    work_item=j,
                )

        logger.debug("Compiling bundle..")
        bundle = WorkPackageBundle(p, all_ext, all_imp, all_jfn)

        return bundle