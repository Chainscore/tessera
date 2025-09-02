from jam.types.work.report import WorkReportHash
from tsrkit_types import Option
from tsrkit_types import Null
import random
from typing import List, cast
from jam.audit.types import RefineVectors, RefineVector, WorkReport

def sample_work_reports_with_nulls(filepath: str, total_items: int = 10, null_count: int = 3) -> List[Option[WorkReport]]:
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

    # Replace selected indices with Null (None in Python)
    for idx in null_indices:
        reports[idx] = Null

    final_report : List[Option[WorkReport]] = reports


    return final_report


# final_sampled_list = sample_work_reports_with_nulls("combine.json", total_items=10, null_count=3)
# print(type(final_sampled_list))

import json

def get_work_package_by_rep_hash(filepath: str, rep_hash: WorkReportHash):

    cnt = 0
    # Load JSON from the given file path
    with open(filepath, "r") as f:
        data = json.load(f)
        refine_vectors = RefineVectors.from_json(data)

    # Iterate through the list and find matching rep_hash
    for vector in refine_vectors:
        cnt = cnt +1
        print("COUNT COUNT COUNT COUNT TO GET SEE THAT REPORT ON COMBINE",cnt)
        vector = cast(RefineVector, vector)
        if vector.rep_hash == rep_hash:
            cnt = 0
            return vector.work_package, vector.core_index, vector.extrinsics

    # If not found
    return Null


# result = get_work_package_by_rep_hash("combine.json", "dc71f2c6f1d2ce6f3cce7362b143aa1939de5d59cc3c042e26e9d1af4f17fe76")
# print(result)