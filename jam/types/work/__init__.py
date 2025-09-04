"""Work types module for the JAM protocol."""

# Execution types
from jam.types.work.execution import (
    WorkExecResult,
    ExecResults,
    RefineLoad,
    WorkDigest,
    WorkDigests,
)

# Item types
from jam.types.work.item import (
    ImportSpec,
    ExtrinsicSpec,
    ImportSpecs,
    ExtrinsicSpecs,
    WorkItem,
)

# Report types
from jam.types.work.report import (
    RefineContext,
    WorkReport,
    WorkDependencies,
    WorkReports,
)

# Package types
from jam.types.work.package import (
    WorkPackageSpec,
    Authorizer,
    WorkItems,
    WorkPackage,
    WorkPackageBundle,
)


from jam.types.work.manifest import (
    Segment,
    Segments,
    MultiSegments,
    Extrinsic,
    Extrinsics,
    MultiExtrinsics,
    Justification,
    Justifications,
    MultiJustifications,
    Assurers,
    SegmentRootLookup,
)

__all__ = [
    # Execution types
    "WorkExecResult",
    "ExecResults",
    "RefineLoad",
    "WorkDigest",
    # Item types
    "ImportSpec",
    "ExtrinsicSpec",
    "ImportSpecs",
    "ExtrinsicSpecs",
    "WorkItem",
    # Report types
    "RefineContext",
    "WorkReport",
    "WorkDependencies",
    # Package types
    "WorkPackageSpec",
    "Authorizer",
    "WorkItems",
    "WorkPackage",
    "WorkPackageBundle",
    # Segment types
    "Segment",
    "Segments",
    "MultiSegments",
    "SegmentRootLookup",
    # Extrinsic
    "Extrinsic",
    "Extrinsics",
    "MultiExtrinsics",
    # Justification
    "Justification",
    "Justifications",
    "MultiJustifications",
    # Collection types
    "WorkDigests",
    "WorkReports",
]
