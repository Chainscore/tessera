from jam.network.protocols.ce_133 import WorkPackageCore
from tsrkit_types import U32, U16, Dictionary, U64, U8, TypedVector, Bytes
from jam.types.work.execution import WorkExecResult, RefineLoad, WorkResult
from jam.types.work.collections import WorkResults
from jam.types.work.report import WorkPackageSpec, RefineContext, WorkReport
from jam.types.protocol.crypto import WorkReportHash
from jam.types.protocol.crypto import OpaqueHash
from jam.types.work.package import WorkPackageBundle, WorkPackage, WorkItems
from jam.types.work.item import WorkItem, ExtrinsicSpecs, ImportSpecs
from jam.types.work.manifest import MultiExtrinsics, MultiSegments, Justifications, MultiJustifications, Segments




work_package_with_core_tet :  WorkPackageCore = WorkPackageCore(work_package=WorkPackage(authorization=0x01,
                                                                                     auth_code_host=U32(42),
                                                                                     code_hash=0x1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d,
                                                                                     params=0xe41c7e902cc9656f0909,
                                                                                     context=RefineContext(anchor=0x7bb3b0aff62a85df490ad26ea4155893e538d256b00cd11634bca3b55d65a9cd,
                                                                                                           state_root=0xb32b442b705f46aa246d7d6cb6108ab240e283daab6e46f51f6e8601a594557d,
                                                                                                           beefy_root=0x1b10153b7da09f577ea2ffbc17d65332de5ac561332f0cae80acac82b514a0cf,
                                                                                                           lookup_anchor=0x2a3f83ba3db640186eb984a23707bff715b3fdcd77a39d11d7c23277de444d13,
                                                                                                           lookup_anchor_slot=U32(33),
                                                                                                           prerequisites=TypedVector[OpaqueHash],
                                                                                     items=WorkItems([WorkItem(service=U32(1),
                                                                                     code_hash=0x738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894,
                                                                                     payload=0x626f6261626f6261,
                                                                                     refine_gas_limit=U64(1000),
                                                                                     accumulate_gas_limit=U64(1000),
                                                                                     import_segments=ImportSpecs([]),
                                                                                     extrinsic=ExtrinsicSpecs([]),
                                                                                     export_count=U16(1))])),
                                                             core_index=U16(1))
                                                            )


work_package_bundle_test :  WorkPackageBundle = WorkPackageBundle(package=WorkPackage(authorization=0x01,
                                                                                     auth_code_host=U32(42),
                                                                                     code_hash=0x1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d,
                                                                                     params=0xe41c7e902cc9656f0909,
                                                                                     context=RefineContext(anchor=0x7bb3b0aff62a85df490ad26ea4155893e538d256b00cd11634bca3b55d65a9cd,
                                                                                                           state_root=0xb32b442b705f46aa246d7d6cb6108ab240e283daab6e46f51f6e8601a594557d,
                                                                                                           beefy_root=0x1b10153b7da09f577ea2ffbc17d65332de5ac561332f0cae80acac82b514a0cf,
                                                                                                           lookup_anchor=0x2a3f83ba3db640186eb984a23707bff715b3fdcd77a39d11d7c23277de444d13,
                                                                                                           lookup_anchor_slot=U32(33),
                                                                                                           prerequisites=TypedVector[OpaqueHash],
                                                                                     items=WorkItems([WorkItem(service=U32(1),
                                                                                                               code_hash=0x738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894,
                                                                                                               payload=0x626f6261626f6261,
                                                                                                               refine_gas_limit=U64(1000),
                                                                                                               accumulate_gas_limit=U64(1000),
                                                                                                               import_segments=ImportSpecs([]),
                                                                                                               extrinsic=ExtrinsicSpecs([]),
                                                                                                               export_count=U16(1))])),
                                                        extrinsics=MultiExtrinsics([]),
                                                        import_segments=MultiSegments([Segments([])]),
                                                        justifications=MultiJustifications([Justifications([])])))



work_report_test : WorkReport = WorkReport(package_spec=WorkPackageSpec(hash=0xf7753f3536d508644c62bca11a38776cf3b4f5807ad74ac92c3ca72e71403278,
                                        length=U32(253),
                                        erasure_root=0x4efdc87587caf141ebac7cd34f6891810ad6906a2f4ab8f19f0a1b714d13f518,
                                        exports_root=0x3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91,
                                        exports_count=U16(1)),
                                        context=RefineContext(anchor=0x7bb3b0aff62a85df490ad26ea4155893e538d256b00cd11634bca3b55d65a9cd,
                                                              state_root=0xb32b442b705f46aa246d7d6cb6108ab240e283daab6e46f51f6e8601a594557d,
                                                              beefy_root=0x1b10153b7da09f577ea2ffbc17d65332de5ac561332f0cae80acac82b514a0cf,
                                                              lookup_anchor=0x2a3f83ba3db640186eb984a23707bff715b3fdcd77a39d11d7c23277de444d13,
                                                              lookup_anchor_slot=U32(33),
                                                              prerequisites=TypedVector[OpaqueHash],
                                        core_index=U16(1),
                                        authorizer_hash=0x1213cfe8b01608fbe50ea08d04c2a6fb0ef8ea48d58303776491827154472be1,
                                        auth_output=0x01,
                                        segment_root_lookup=Dictionary({}),
                                        results=WorkResults([WorkResult(service_id=U32(1), code_hash=0x738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894, payload_hash=0xad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af, accumulate_gas=U64(1000), result=WorkExecResult(()), refine_load=RefineLoad(gas_used=U64(29), imports=U16(0), extrinsic_count=U8(0), extrinsic_size=U64(0), exports=U16(1)))]),
                                        auth_gas_used=U64(7)))

work_report_hash_test : WorkReportHash = 0xfd94f3be29c6036e48f921baa9f4ec2fb0a90d7cdc92e220da6dff8628717c59

