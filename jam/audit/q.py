import json
import random

from typing import List, cast

from tsrkit_types import Option, Null

from jam.types.work.report import WorkReportHash
from tests.unit.incore.types import RefineVectors, RefineVector, WorkReport


def sample_work_reports_with_nulls(
    filepath: str, total_items: int = 10, null_count: int = 3
) -> List[Option[WorkReport]]:
    # Load JSON file
    with open(filepath, "r") as f:
        data = json.load(f)
        refine_vectors = RefineVectors.from_json(data)

    # Extract first `total_items` work reports
    reports = []
    for vector in refine_vectors[:total_items]:
        vector = cast(RefineVector, vector)
        reports.append(vector.work_rep)

    # Pick random indices to replace with Null
    null_indices = random.sample(range(len(reports)), min(null_count, len(reports)))

    # return reports

    # Replace selected indices with Null (None in Python)
    for idx in null_indices:
        reports[idx] = Null

    final_report : List[Option[WorkReport]] = reports

    return final_report

def get_work_package_by_rep_hash(filepath: str, rep_hash: WorkReportHash):
    cnt = 0
    # Load JSON from the given file path
    with open(filepath, "r") as f:
        data = json.load(f)
        refine_vectors = RefineVectors.from_json(data)

    # Iterate through the list and find matching rep_hash
    for vector in refine_vectors:
        cnt = cnt + 1
        vector = cast(RefineVector, vector)
        if vector.rep_hash == rep_hash:
            cnt = 0
            return vector.work_package, vector.core_index, vector.extrinsics

    # If not found
    return Null

