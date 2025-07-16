import json
import os
from typing import Any, Dict
import random

os.environ["JAM_CHAIN_SPEC"] = "full"

from tsrkit_types import Bytes, Null, Uint
from tsrkit_types.option import Option
from tsrkit_types.sequences import TypedArray, TypedVector

from jam.types.protocol.core import CoreIndex, ErasureRoot, ExportsRoot, Gas, ServiceId, TimeSlot, WorkPackageHash
from jam.types.protocol.crypto import BeefyRoot, HeaderHash, OpaqueHash, StateRoot
from jam.types.state.rho import OptionalWorkReportState, Rho, WorkReportState
from jam.types.work.execution import RefineContext, RefineLoad, WorkExecResult, WorkResult, WorkResults
from jam.types.work.item import ExtrinsicSpec, ExtrinsicSpecs, ImportSpec, ImportSpecs, WorkItem
from jam.types.work.package import Authorizer, WorkItems, WorkPackage, WorkPackageSpec
from jam.types.work.manifest import SegmentRootLookup
from jam.types.work.report import WorkReport, WorkReports
from jam.utils.constants import CORE_COUNT


def work_package_from_json(data: Dict[str, Any]) -> WorkPackage:
    """Create a WorkPackage object from a JSON dictionary."""

    work_items = WorkItems([
        WorkItem(
            service=ServiceId(item['service']),
            code_hash=OpaqueHash(bytes.fromhex(item['code_hash'])),
            payload=Bytes(bytes.fromhex(item['payload'])),
            refine_gas_limit=Gas(item['refine_gas_limit']),
            accumulate_gas_limit=Gas(item['accumulate_gas_limit']),
            import_segments=ImportSpecs([
                ImportSpec(
                    tree_root=OpaqueHash(bytes.fromhex(seg['tree_root'])),
                    index=Uint[16](seg['index'])
                ) for seg in item['import_segments']
            ]),
            extrinsic=ExtrinsicSpecs([
                ExtrinsicSpec(
                    hash=OpaqueHash(bytes.fromhex(ext['hash'])),
                    len=Uint[32](ext['len'])
                ) for ext in item['extrinsic']
            ]),
            export_count=Uint[16](item['export_count'])
        ) for item in data['items']
    ])

    context_data = data['context']
    refine_context = RefineContext(
        anchor=HeaderHash(bytes.fromhex(context_data['anchor'])),
        state_root=StateRoot(bytes.fromhex(context_data['state_root'])),
        beefy_root=BeefyRoot(bytes.fromhex(context_data['beefy_root'])),
        lookup_anchor=HeaderHash(bytes.fromhex(context_data['lookup_anchor'])),
        lookup_anchor_slot=TimeSlot(context_data['lookup_anchor_slot']),
        prerequisites=TypedVector[OpaqueHash](
            [OpaqueHash(bytes.fromhex(p)) for p in context_data['prerequisites']]
        )
    )

    authorizer_data = data['authorizer']
    authorizer = Authorizer(
        code_hash=OpaqueHash(bytes.fromhex(authorizer_data["code_hash"])),
        params=Bytes(bytes.fromhex(authorizer_data["params"]))
    )

    return WorkPackage(
        authorization=Bytes(bytes.fromhex(data['authorization'])),
        auth_code_host=ServiceId(data['auth_code_host']),
        authorizer=authorizer,
        context=refine_context,
        items=work_items
    )

def work_report_from_json(data: Dict[str, Any]) -> WorkReport:
    """Create a WorkReport object from a JSON dictionary."""

    # --- Build WorkPackageSpec --- #
    spec_data = data['package_spec']
    package_spec = WorkPackageSpec(
        hash=WorkPackageHash(bytes.fromhex(spec_data['hash'])),
        length=Uint[32](spec_data['length']),
        erasure_root=ErasureRoot(bytes.fromhex(spec_data['erasure_root'])),
        exports_root=ExportsRoot(bytes.fromhex(spec_data['exports_root'])),
        exports_count=Uint[16](spec_data['exports_count'])
    )

    # --- Build RefineContext --- #
    context_data = data['context']
    refine_context = RefineContext(
        anchor=HeaderHash(bytes.fromhex(context_data['anchor'])),
        state_root=StateRoot(bytes.fromhex(context_data['state_root'])),
        beefy_root=BeefyRoot(bytes.fromhex(context_data['beefy_root'])),
        lookup_anchor=HeaderHash(bytes.fromhex(context_data['lookup_anchor'])),
        lookup_anchor_slot=TimeSlot(context_data['lookup_anchor_slot']),
        prerequisites=TypedVector[OpaqueHash](
            [OpaqueHash(bytes.fromhex(p)) for p in context_data['prerequisites']]
        )
    )

    # --- Build WorkResults --- #
    work_results = WorkResults([
        WorkResult(
            service_id=ServiceId(result['service_id']),
            code_hash=OpaqueHash(bytes.fromhex(result['code_hash'])),
            payload_hash=OpaqueHash(bytes.fromhex(result['payload_hash'])),
            accumulate_gas=Gas(result['accumulate_gas']),
            result=WorkExecResult.from_json(result['result']),
            refine_load=RefineLoad(
                gas_used=Gas(result['refine_load']['gas_used']),
                imports=Uint[32](result['refine_load']['imports']),
                extrinsic_count=Uint[32](result['refine_load']['extrinsic_count']),
                extrinsic_size=Uint[32](result['refine_load']['extrinsic_size']),
                exports=Uint[32](result['refine_load']['exports'])
            )
        ) for result in data['results']
    ])

    # --- Build Final WorkReport --- #
    return WorkReport(
        package_spec=package_spec,
        context=refine_context,
        core_index=CoreIndex(data['core_index']),
        authorizer_hash=OpaqueHash(bytes.fromhex(data['authorizer_hash'])),
        auth_output=Bytes(bytes.fromhex(data['auth_output'])),
        segment_root_lookup=SegmentRootLookup(data['segment_root_lookup']),
        results=work_results,
        auth_gas_used=Gas(data['auth_gas_used'])
    )

def main():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, 'vectors/dummy_wp.json')

    print(f"Looking for file at: {file_path}")
    if not os.path.exists(file_path):
        print(f"❌ File not found at: {file_path}")
        return

    with open(file_path, 'r') as f:
        raw_data = json.load(f)

    wp_dict={}
    wr_dict={} # Consists of wr_hash to workPackages
    # Corrected dummy_rho initialization
    dummy_rho = Rho([OptionalWorkReportState(None) for _ in range(CORE_COUNT)])

    # print(dummy_rho)
    available_wrs=WorkReports([])
    if raw_data:
        # --- Process WorkPackage --- #
        for package in raw_data:
            package_json = package['work_package']
            random_core=random.randrange(0, CORE_COUNT+1)
            work_package_obj = work_package_from_json(package_json)
            try:
                encoded_package = work_package_obj.encode().hex()
                wp_dict[encoded_package] = work_package_obj
            except Exception as e:
                print(f"Failed to encode WorkPackage object: {e}")


            # --- Process WorkReport --- #
            report_json = package['work_rep']
            report_json['core_index']=CoreIndex(random_core)
            work_report_obj = work_report_from_json(report_json)
            try:
                encoded_report = work_report_obj.encode().hex()
                wr_dict[encoded_report] = work_package_obj
                available_wrs.append(work_report_obj)
                # Corrected assignment to dummy_rho
                dummy_rho[random_core]=OptionalWorkReportState(WorkReportState(
                    report=work_report_obj,
                    timeout=TimeSlot(20)))
            except Exception as e:
                print(f"Failed to encode WorkReport object: {e}")

    for index in enumerate(dummy_rho):
        if index:
            print(index)


if __name__ == "__main__":
    main()
