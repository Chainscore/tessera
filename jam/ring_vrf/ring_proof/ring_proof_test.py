#Take the test file, get the ring of public keys, secret_t, and block producer index
# import the vects, polys, commmitmt funcs from columns and get those results
#import the  constraints and get the contraints passing the witness, fixed cols
#import the cosntraint agg and get the aggregated cosntraint poly
# import the quotient poly get the quotient poly
# import the linearization poly get the linearization poly
#import the agg poly funcs and get the proof constructed
# imort the verifier logic and get the proof verification ;check with all the test vectors

import json
import time
start_time=time.time()
from jam.ring_vrf.ring_proof.pcs.load_powers import g1_points, g2_points
from jam.ring_vrf.ring_proof.transcript.phases import phase1_alphas
from jam.ring_vrf.ring_proof.transcript.transcript import Transcript
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint
from jam.ring_vrf.ring_proof.short_weierstrass.curve import ShortWeierstrassCurve as sw
from jam.ring_vrf.ring_proof.constants import Blinding_Base, S_PRIME, OMEGA_2048, SeedPoint
from jam.ring_vrf.ring_proof.columns.columns import WitnessColumnBuilder, PublicColumnBuilder
from jam.ring_vrf.ring_proof.constraints.constraints import RingConstraintBuilder
from jam.ring_vrf.ring_proof.helpers import Helpers as H
from py_ecc.optimized_bls12_381 import  normalize as nm
from jam.ring_vrf.ring_proof.constraints.aggregation import aggregate_constraints
from jam.ring_vrf.ring_proof.proof.quotient_poly import QuotientPoly
from jam.ring_vrf.ring_proof.proof.linearization_poly import LAggPoly
from jam.ring_vrf.ring_proof.proof.aggregation_poly_and_proof_gtn import AggPoly
from jam.ring_vrf.ring_proof.verfiey import Verify
from jam.ring_vrf.ring_proof.constants import D_512 as D

import json
import os
def test_ring_proof():
    file_path = '/home/siva/PycharmProjects/tessera_JAM_VRF/tests/unit/vrf/data/ark-vrf/bandersnatch_ed_sha512_ell2_ring.json'
    with open(file_path, 'r') as f:
        data = json.load(f)

    for index in range(len(data)):

        if index < 0 or index >= len(data):
            raise IndexError("Index out of range")

        item = data[index]

        secret_BA = item['blinding']

        secret_B = bytes.fromhex(secret_BA)

        secret_t = int.from_bytes(secret_B, 'little')

        # print("secret_t:", secret_t)

        block_producer = item['pk']

        pk_ring = item['ring_pks']

        pk_list = []
        pk_x_y_list = []

        frm = 0
        to = 64
        # print(len(pk_ring))
        for i in range(len(pk_ring) // 64):
            pk_list.append(pk_ring[frm:to])
            frm = to
            to += 64

        count = 0
        for string in pk_list:
            try:
                pk = BandersnatchPoint.string_to_point(string)
                pk_x_y_list.append(sw.from_twisted_edwards((pk.x, pk.y)))
            except ValueError as e:
                count += 1

        producer_index = pk_list.index(block_producer)

        # single test file

        # buillding the vectors, polys, commitments
        f_c_s = PublicColumnBuilder()
        List_of_PK = pk_x_y_list
        fixed_cols = f_c_s.build(List_of_PK)
        s_v = fixed_cols[-1].evals
        witness_obj = WitnessColumnBuilder(List_of_PK, s_v, producer_index, secret_t)
        witness_res = witness_obj.build()
        witness_relation_res = witness_obj.result(Blinding_Base)
        Result_plus_Seed = witness_obj.result_p_seed(witness_relation_res)

        # print("RESULT:", witness_relation_res)
        # for each in witness_res:
        #     print("witness cmts", each.commitment)

        # building constraints
        constraints = RingConstraintBuilder(Result_plus_Seed, fixed_cols[0].coeffs, fixed_cols[1].coeffs,
                                            fixed_cols[2].coeffs, witness_res[0].coeffs, witness_res[1].coeffs,
                                            witness_res[2].coeffs, witness_res[3].coeffs)

        constraint_dict = constraints.compute()
        # print("consraunts:", constraint_dict)

        # consraints Agrregation

        # convert the g2 points for fs
        fixed_col_commits = [H.to_int(nm(fixed_cols[0].commitment)), H.to_int(nm(fixed_cols[1].commitment)),
                             H.to_int(nm(fixed_cols[2].commitment))]

        ws = witness_res
        witness_commitments = [H.to_int(nm(ws[0].commitment)), H.to_int(nm(ws[-1].commitment)),
                               H.to_int(nm(ws[1].commitment)), H.to_int(nm(ws[2].commitment))]

        vk = {
            'g1': g1_points[0],
            'g2': H.altered_points(g2_points),
            'commitments': fixed_col_commits
        }

        t = Transcript(S_PRIME, b"Bandersnatch_SHA-512_ELL2")
        t, alphas = phase1_alphas(t, vk, witness_relation_res, witness_commitments)
        # print("Alphas Got:", alphas)
        cd = constraint_dict
        c_polys = [cd[val] for val in cd]
        # print("is 7:", len(c_polys))
        # print("C_POLYS:", c_polys)
        # print("Inputs for alphas:", (vk, witness_relation_res, witness_commitments))
        C_agg = aggregate_constraints(c_polys, alphas, OMEGA_2048, S_PRIME)
        # print("constraint_agg_res:", C_agg)

        # quotient_poly generation

        qp = QuotientPoly()
        Q_p, C_q = qp.quotient_poly(C_agg)
        C_q_nm = nm(C_q)
        # print("Quotuient_cmt:", C_q)
        # print("Quoteint_cmt_nm", C_q_nm)

        # relevant_poly+ l_agg poly evaluations

        l_obj = LAggPoly(t, H.to_int(C_q_nm), fixed_cols, ws, alphas)
        current_t, zeta, rel_poly_evals, l_agg, zeta_omega, l_zw = l_obj.l_agg_poly()

        # print("zeta:", zeta)
        # print("Relevant_poly_evals:", rel_poly_evals)
        # print("L_AGG:", l_agg)
        # print("zeta_omega:", zeta_omega)
        # print("l_z_w:", l_zw)

        # agg_poly, 2 openings and proof construction

        obj = AggPoly(current_t, zeta, fixed_cols, ws, Q_p, C_q, rel_poly_evals, l_agg, zeta_omega, l_zw)

        cf_vs, proof_ptr, proof_bs = obj.construct_proof()
        end_time = time.time()

        # print("Proof point representation:", proof_ptr)
        # print("proof_byte_string:", proof_bs)

        assert proof_bs == item['ring_proof']
        print(f"Is proof {index} matching:", proof_bs == item['ring_proof'])

        # proof verification
        cnd_res = witness_relation_res

        vfr = Verify(proof_ptr, vk, fixed_cols, cnd_res, Result_plus_Seed, SeedPoint, D)
        # print("proof1:", vfr.evaluation_of_linearization_poly_at_zeta_omega())
        # print("prioof2:", vfr.evaluation_of_quotient_poly_at_zeta())
        print(f"Is signature {index} valid:", vfr.is_signtaure_valid())
        print(f"Test_Case {index}:✅")





