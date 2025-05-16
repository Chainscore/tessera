import time
start_time=time.time()
from jam.ring_vrf.ring_proof.constants import S_PRIME
from jam.ring_vrf.ring_proof.polynomial.ops import poly_add, poly_scalar
from jam.ring_vrf.ring_proof.transcript.phases import phase3_nu_vector
from jam.ring_vrf.ring_proof.pcs.kzg import KZG
from jam.ring_vrf.ring_proof.helpers import  Helpers as H

kzg=KZG.default()

class AggPoly:

    def __init__(self, cur_t, zta, fixed_cols, witness_cols, quotient_poly, quotient_cmt, poly_evals, l_Agg, zw, l_agg_zw):

        self.zeta= zta
        (self.P_x_zeta, self.P_y_zeta, self.s_zeta, self.b_zeta,
         self.acc_ip_zeta, self.acc_x_zeta, self.acc_y_zeta)= list(poly_evals.values())
        self.l_agg = l_Agg
        self.zeta_omega = zw
        self.l_agg_at_zeta_omega= l_agg_zw
        self.cf_vectors= phase3_nu_vector(cur_t,list(poly_evals.values()), l_agg_zw)
        self.fs= fixed_cols
        self.ws= witness_cols
        self.Q_p= quotient_poly
        self.C_q= quotient_cmt


    # get the aggregated poly
    def aggregated_poly(self):

        poly_I = [self.fs[0].coeffs, self.fs[1].coeffs,self.fs[2].coeffs, self.ws[0].coeffs, self.ws[3].coeffs ,self.ws[1].coeffs,self.ws[2].coeffs, self.Q_p]
        V_list = self.cf_vectors

        # print("V_list:", V_list)

        agg_poly = [0]
        for i in range(len(poly_I)):
            agg_poly = poly_add(agg_poly, poly_scalar(poly_I[i], V_list[i], S_PRIME), S_PRIME)
        return agg_poly

    #two proof openings
    def proof_contents_phi(self):
        """
        input:agg_poly, liner_poly, zeta, zeta_omega
        output: Phi_zeta, phi_zeta_omega
        """
        agg_p=self.aggregated_poly()
        # print("agg_p:", agg_p)
        phi_z_opening = kzg.open(agg_p, self.zeta)  # take only proof
        # print("Agg at zeta in proover side:", phi_z_opening.y)
        phi_zw_opening= kzg.open(self.l_agg, self.zeta_omega)  # take only proof
        # print("L_Zeta_omega in proover side:", phi_zw_opening.y)
        return phi_z_opening, phi_zw_opening,phi_z_opening.proof, phi_zw_opening.proof

    def construct_proof(self):
        """
        input: commitments, poly_evaluations
        output: proof
        """
        opening1, opening2, phi_z, phi_zw= self.proof_contents_phi()
        C_b, C_acc_ip,C_acc_x, C_acc_y= self.ws[0].commitment, self.ws[3].commitment, self.ws[1].commitment, self.ws[2].commitment

        #Proof point representation
        Proof_P_rpr= [C_b, C_acc_ip, C_acc_x, C_acc_y, self.P_x_zeta, self.P_y_zeta, self.s_zeta, self.b_zeta, self.acc_ip_zeta, self.acc_x_zeta, self.acc_y_zeta,self.C_q, self.l_agg_at_zeta_omega, phi_z, phi_zw]

        #Proof Byte String Representation
        Proof_B_Str_rpr= H.bls_g1_compress(C_b)+H.bls_g1_compress(C_acc_ip)+ H.bls_g1_compress(C_acc_x)+ H.bls_g1_compress(C_acc_y)+ H.to_bytes(self.P_x_zeta)+ H.to_bytes(self.P_y_zeta)+ H.to_bytes(self.s_zeta)+H.to_bytes( self.b_zeta)+ H.to_bytes(self.acc_ip_zeta)+ H.to_bytes(self.acc_x_zeta)+H.to_bytes( self.acc_y_zeta) +H.bls_g1_compress(self.C_q)+ H.to_bytes(self.l_agg_at_zeta_omega)+ H.bls_g1_compress(phi_z)+ H.bls_g1_compress(phi_zw)
        return self.cf_vectors, Proof_P_rpr,Proof_B_Str_rpr #, fs[0].commitment, fs[1].commitment, fs[2].commitment


# alphas=[28771376604832841235502705186578417253715647647950175672206128727189795055588, 22425742425595723507200758501495484441155088683175722144669039508980737859762, 48071804566211453263606689239439662666418582599552265147053783192355059291811, 47090774944046929692569906533139957392906430096933536633869409870908786060167, 30164629497538750127782814393885000871904620052477176764872541970640491648857, 28625392876009170934567064722328934562837146443519373929493200003750359936136, 41635967665677668819965154879429560258561339252244303639899597978874982091699]
# Zeta= [42595660466703795432761140260372523142532524796174249596200169995982693529761]
# vectors=[47743891525884372843199201544696943033147147328563836360547568607407226946830, 43838575802653357475607244659407568674450052097188199032968935069280549969881, 11380023864678768444875897429102633851409112248919603185923402562286456416349, 28198320119941590251732780067331425806063744611229489479348591901872199258562, 51656981723654202855462715747035230325168702689004432940744786178055972869838, 37074871960706300079782785132715703637574483165607552754473154666950479185986, 49524909988050044029328069641989619792432761752862265428182106382737042538779, 10552014230776434796607380717910796575196594550522251381924901953053434643768]
