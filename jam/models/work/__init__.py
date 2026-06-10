"""Work types module for the JAM protocol."""

# Execution types
from jam.models.work.execution import (
    WorkExecResult,
    ExecResults,
    RefineLoad,
    WorkDigest,
    WorkDigests,
)

# Item types
from jam.models.work.item import (
    ImportSpec,
    ExtrinsicSpec,
    ImportSpecs,
    ExtrinsicSpecs,
    WorkItem,
)

# Report types
from jam.models.work.report import (
    RefineContext,
    WorkReport,
    WorkDependencies,
    WorkReports,
)

from jam.models.work.guarantee import (
    ValidatorSignature,
    ValidatorSignatures,
    ReportGuarantee,
    GuaranteesExtrinsic,
)

# Package types
from jam.models.work.package import (
    WorkPackageSpec,
    Authorizer,
    WorkItems,
    WorkPackage,
    WorkPackageBundle,
)


from jam.models.work.manifest import (
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
    "ValidatorSignature",
    "ValidatorSignatures",
    "ReportGuarantee",
    "GuaranteesExtrinsic",
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
