"""Work types module for the JAM protocol."""

# Execution types
from jam.types.work.execution import (
    WorkExecResult,
    ExecResults,
    RefineLoad,
    WorkResult, WorkResults,
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
    WorkDependencies, WorkReports,
)

# Package types
from jam.types.work.package import (
    WorkPackageSpec,
    Authorizer,
    WorkItems,
    WorkPackage,
    WorkPackageBundle,
)

# Segment types
from jam.types.work.segments import (
    Segment,
    Segments,
    MultiSegments,
    SegmentRootLookup,
)


__all__ = [
    # Execution types
    "WorkExecResult",
    "ExecResults", 
    "RefineLoad",
    "WorkResult",
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
    # Collection types
    "WorkResults",
    "WorkReports",
] 