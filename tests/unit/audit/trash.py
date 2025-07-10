# @patch('jam.audit.audit.CURRENT_TIME')
# @patch('jam.audit.audit.Assurances.transition')
# @patch('jam.audit.audit.bandersnatch_f')
# def test_tiny_spec_full_audit_in_first_tranche(mock_vrf_sig, mock_assurance_transition, mock_current_time, tiny_spec_state):
#     """Tiny spec scenario: 2 WRs fully audited by 6 validators in tranche 0."""
#     finalized_header = Header(slot=1, parent=Hash(bytes(32)), parent_state_root=Hash(bytes(32)), extrinsic_hash=Hash(bytes(32)))
#     mock_current_time.return_value = (MOCK_SLOT_PERIOD * finalized_header.slot) + 3

#     mock_vrf_sig.return_value = bytes(96)
#     mock_assurance_transition.return_value = (tiny_spec_state, set())

#     # We provide the tiny_spec_state and an empty set for assurances to the constructor.
#     auditing = AuditingAndJudgement(current_state=tiny_spec_state, current_assurances=set())

#     with patch('jam.audit.audit.SLOT_PERIOD', MOCK_SLOT_PERIOD), \
#          patch('jam.audit.audit.AUDIT_PERIOD', MOCK_AUDIT_PERIOD):

#         tranche_index = auditing.generate_tranche_index(finalized_header)
#         assert tranche_index == 0

#         reports_to_audit = auditing.report_to_be_audit()
#         assert len(reports_to_audit) == 2

#         total_work_assignments = {}
#         for i in range(6):
#             workload = auditing.vrs_func(finalized_header, ValidatorIndex(i), tranche_index=0)
#             for core_index, report in workload:
#                 if report.work_package_hash not in total_work_assignments:
#                     total_work_assignments[report.work_package_hash] = set()
#                 total_work_assignments[report.work_package_hash].add(i)

#         assert len(total_work_assignments) == 2
#         assert len(total_work_assignments[Hash(b'work_report_0')]) > 0
#         assert len(total_work_assignments[Hash(b'work_report_1')]) > 0

#         print("\nTest Passed: Tiny spec scenario correctly assigns work in Tranche 0.")
#         print(f"Work Report 0 assigned to: {total_work_assignments[Hash(b'work_report_0')]}")
#         print(f"Work Report 1 assigned to: {total_work_assignments[Hash(b'work_report_1')]}")
