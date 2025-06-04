"""Work-related types for the JAM protocol."""

from jam.types.work.refine_context import RefineContext
from jam.types.work.item import ImportSpec, ExtrinsicSpec, WorkItem
from jam.types.work.package import Authorizer, WorkPackage
from jam.types.work.report import (
    WorkExecResult,
    WorkResult,
    WorkPackageSpec,
    WorkPackageBundle,
    SegmentRootLookup,
    WorkReport,
    WorkDependencies,
    WorkReports,
)
from jam.types.work.segment import Segment, Segments, MultiSegments

__all__ = [
    # Refine context
    "RefineContext",
    # Work item
    "ImportSpec",
    "ExtrinsicSpec",
    "WorkItem",
    # Work package
    "Authorizer",
    "WorkPackage",
    # Work report
    "WorkExecResult",
    "WorkResult",
    "WorkPackageSpec",
    "WorkPackageBundle",
    "SegmentRootLookup",
    "WorkReport",
    "WorkDependencies",
    "WorkReports",
    # Segments
    "Segment",
    "Segments",
    "MultiSegments",
]
