import json

from tests.unit.incore.types import BundleVector


def fetch_vectors(st: int, end: int, vectors):
    for i in range(st, end):
        with open(f"vectors/bundles/bundles-{i:03d}.json", "r") as f:
            data = json.load(f)
            bundle_vec = BundleVector.from_json(data)
            vectors.append(bundle_vec)