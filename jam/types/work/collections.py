"""Work collection types for the JAM protocol."""

from tsrkit_types.sequences import TypedVector

from jam.types.work.execution import WorkResult
from jam.types.work.report import WorkReport


WorkResults = TypedVector[WorkResult]  # Vector of Work Results

WorkReports = TypedVector[WorkReport]  # Vector of Work Reports 