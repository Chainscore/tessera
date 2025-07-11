import asyncio
from typing import Optional, Tuple, List
from tsrkit_types import Bytes, TypedVector, Null, Uint, Option, Dictionary
from jam.audit.utils import signature_pvt
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
from jam.types.work.report import WorkReport
from jam.utils.constants import SIGNING_CONTEXTS
from jam.types.protocol.crypto import BandersnatchPublic, Ed25519Public
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.types.block.header import Header
from jam.utils.shuffle import shuffle
from jam.types.protocol.core import CoreIndex, WorkReportHash
from jam.types import (
    BandersnatchVrfSignature,
    Ed25519Public,
    Hash,
    HeaderHash,
    StateRoot,
    OpaqueHash,
    EpochMark,
    TimeSlot, ValidatorIndex,
    TicketsMark
)

from jam.types.work.package import WorkPackage

import json

report = TypedVector[Option[WorkReport]]([])
print(len(report))




"""------------------------------- tranche condition when the  ------------------------------- """


OffendersMark = TypedVector[Ed25519Public]


header1 = Header(parent=Bytes.fromhex("5c743dbc514284b2ea57798787c5a155ef9d7ac1e9499ec65910a7a3d65897b7"),
                parent_state_root=Bytes.fromhex("2591ebd047489f1006361a4254731466a946174af02fe1d86681d254cfd4a00b"),
                extrinsic_hash=Bytes.fromhex("74a9e79d2618e0ce8720ff61811b10e045c02224a09299f04e404a9656e85c81"),
                slot=TimeSlot(42),
                epoch_mark=Bytes(b""),
                tickets_mark= Null,
                offenders_mark=OffendersMark([
                    Bytes[32](Bytes.fromhex("ad93247bd01307550ec7acd757ce6fb805fcf73db364063265b30a949e90d933"))
                ]),
                author_index = ValidatorIndex(3),
                entropy_source = Bytes.fromhex("ae85d6635e9ae539d0846b911ec86a27fe000f619b78bcac8a74b77e36f6dbcf49a52360f74a0233cea0775356ab0512fafff0683df08fae3cb848122e296cbc50fed22418ea55f19e55b3c75eb8b0ec71dcae0d79823d39920bf8d6a2256c5f"),
                seal= Bytes.fromhex("31dc5b1e9423eccff9bccd6549eae8034162158000d5be9339919cc03d14046e6431c14cbb172b3aed702b9e9869904b1f39a6fe1f3e904b0fd536f13e8cac496682e1c81898e88e604904fa7c3e496f9a8771ef1102cc29d567c4aad283f7b0")
                )

optional_report : List[Option[WorkReportHash]] = ([
    Bytes.fromhex("8d94fa1e8b4a1158fce4219c5e869563e2db34356054df2bef62f6798d00f613"),
    Bytes.fromhex("de2a1700d01bde4935c2b3956dbef0641dd4cc060c2fd286e1b48a2524db8502"),
    Null,
    Bytes.fromhex("ca8531d192c72c575dbddb37d4afbbaa35a06d523d3a3ae99dfcd1b73d99b783"),
    Null,
    Bytes.fromhex("8f4219d15c80bbf186bc0be610c7e6536aebadca496878a534c7264f74743e99"),
    Null,
    Bytes.fromhex("78ae8779c9feb5f73a8f5187d05fb983bf2682d07af0d5655e034123847554dc"),
    Bytes.fromhex("f1110d84f9c3f87130ce571960b1eae063c200ef9631bf7cc6d11dfec33dd933"),
    Bytes.fromhex("ca574b0eedaff7a545c8d96edb95740cef59eb50bcab6ca0f33f520ae861ba25")
])



def validator_announcement_statement( assign_report: List[Tuple[CoreIndex, WorkReportHash]], header: Header, ed25519_public: Ed25519Public, tranche: Uint) -> set[Bytes[64]]:
    validator_announcement_set: set[Bytes[64]] = set()

    signing_context = Bytes(SIGNING_CONTEXTS["announce"])

    header_hash = Bytes(Hash.blake2b(header.encode()))

    context = signing_context + Bytes(tranche) + header_hash

    for c, r in assign_report:
        context = context + Bytes(c.encode() + Hash.blake2b(r.encode())).encode()
        signature = signature_pvt(key=ed25519_public, context=context)
        validator_announcement_set.add(signature)
        context = signing_context + Bytes(tranche) + header_hash

    return validator_announcement_set

def vrf_signature_bandersnatch(entropy_source: BandersnatchVrfSignature, bandersnatch_key: BandersnatchPublic) -> Bytes[96]:
    vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)

    entropy_vrf_proof = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(entropy_source.encode()))[:32]
    random_quantity = Bytes(SIGNING_CONTEXTS["audit"]) + entropy_vrf_proof  # Xv + y(Hv)

    signature = signature_pvt(key=bandersnatch_key, context=random_quantity)

    return signature

def vrs_func(entropy_source: BandersnatchVrfSignature, bandersnatch_key: BandersnatchPublic, pre_report: List[Option[WorkReport]]) -> List[Tuple[CoreIndex, WorkReportHash]]:

    vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
    entropy = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(vrf_signature_bandersnatch(entropy_source=entropy_source, bandersnatch_key=bandersnatch_key)))[:32]

    pre_audit_reports = pre_report
    core_indexes = list[Tuple[CoreIndex, Option[WorkReportHash]]]([])
    for c, w_r in enumerate(pre_audit_reports):
        core_indexes.append((CoreIndex(c), w_r))

    # ------------------------------------- audit size array and shuffle --------------------------------------------
    array_index = TypedVector[Uint[32]]([])
    for i in range(len(pre_audit_reports)):
        array_index.append(Uint[32](i))

    shuffle_array = shuffle(entropy, array_index)

    # ------------------------------------------ updated shuffle auditing list -------------------------------------
    lookup = dict(core_indexes)
    updated_array: List[Tuple[Uint[16], Option[WorkReportHash]]] = [(Uint[16](i), lookup[i]) for i in shuffle_array]

    # ------------------------------------------ take initial 10 values --------------------------------------------
    # Eq. 17.5 : ao = {(c, w) | (c, w) E p... + 10, w != Phi }
    shuffle_not_null = [(c, w) for (c, w) in updated_array if w is not Null][:5]

    return shuffle_not_null


# output = vrs_func(entropy_source="f7caffd3498473b08ab9de28ba3bd76d94f3fe47acc96e6e0111dfe301ba4d0bc7b3a95ebf21a76fb76102c13fdf9947c6c243d71b9893fae0b9adf94aa83f0a81b4566c15c796a79a4e124971130cba959c03066efba2161334cedc0d02151a", bandersnatch_key=Bytes.fromhex("ff71c6c03ff88adb5ed52c9681de1629a54e702fc14729f6b50d2f0a76f185b3"), pre_report=optional_report)
# print( "final answer =>", output)

# answer  = validator_announcement_statement(assign_report=output, header=header1, ed25519_public=Bytes.fromhex("4418fb8c85bb3985394a8c2756d3643457ce614546202a2f50b093d762499ace") ,tranche=Uint(0))
# print(len(answer), answer)


# from jam.audit.vectors.packages import packages
# for i in packages:
#     print(WorkPackage.from_json(i))



#
# def judgment( q:List[Option[WorkReport]]):
#
#     assigned_report = vrs_func(entropy_source="f7caffd3498473b08ab9de28ba3bd76d94f3fe47acc96e6e0111dfe301ba4d0bc7b3a95ebf21a76fb76102c13fdf9947c6c243d71b9893fae0b9adf94aa83f0a81b4566c15c796a79a4e124971130cba959c03066efba2161334cedc0d02151a", bandersnatch_key=Bytes.fromhex("ff71c6c03ff88adb5ed52c9681de1629a54e702fc14729f6b50d2f0a76f185b3"), pre_report= q)
#     print("assigned_report => ",assigned_report)
#
#     # announcement
#     announcement = validator_announcement_statement(assign_report=assigned_report, header=Header(data), ed25519_public=node.ed_key, tranche=Uint(0))
#     print("announcement => ", announcement)
#
#     judgment_set : set[bool] = set()
#
#     from jam.work_package.processor import Processor
#     from jam.network.node import Node
#     node = Node
#
#     process = Processor(node)
#     for c, r in assigned_report:
#         # fetch work package
#         for i in packages:
#             if r["package_spec"]["hash"] == Hash.blake2b(WorkPackage.from_json(i).encode()):
#                 bundle = WorkPackage.from_json(i)
#                 w_r, wr_hash = process.process_bundle(core=c, bundle=bundle, sr_lookup=Dictionary({}))
#                 if wr_hash == Hash.blake2b(r.encode()):
#                     judgment_set.add(True)
#                 else:
#                     judgment_set.add(False)
#
#     return judgment

#
#
# from jam.audit.vectors.reports import reports
#
# optional_data_reports : list[Option[WorkReport]] = []
# for i in reports:
#     optional_data_reports.append(WorkReport.from_json(i))
#
#
# judgment = judgment(q=optional_data_reports)

# Here we check each report and created a list of audited reports


# def judgment(self, q:TypedVector[Option[WorkReport]], node: Node, header: Header):
#
#     assigned_report = self.vrs_func(entropy_source="f7caffd3498473b08ab9de28ba3bd76d94f3fe47acc96e6e0111dfe301ba4d0bc7b3a95ebf21a76fb76102c13fdf9947c6c243d71b9893fae0b9adf94aa83f0a81b4566c15c796a79a4e124971130cba959c03066efba2161334cedc0d02151a", bandersnatch_key=node.ed_pvt_key, pre_report= q)
#     announcement = self.validator_announcement_statement(assign_report=assigned_report, header=header, ed25519_public=node.ed_key, tranche=Uint(0))
#     judgment : set[bool] = set()
#
#     return judgment
