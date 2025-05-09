import math
import hashlib, struct
from typing import Any
from jam.ring_vrf.ring_proof.constants import S_PRIME
from jam.ring_vrf.ring_proof.helpers import bls_g1_compress, to_int
from typing import Any, Tuple
from py_ecc.bls12_381 import curve_order

from jam.ring_vrf.ring_proof.preprocessing import C_px_nm, C_py_nm, C_s_nm
from jam.ring_vrf.ring_proof.prover_witness_polynomials import Result_point, C_b_v_nm, C_acc_ip_nm, \
    C_acc_x_nm, C_acc_y_nm

# (QuadExtField(352701069587466618187139116011060144890029952792775240219908644239793785735715026873347600343865175952761926303160
#               + 3059144344244213709971259814753781636986470325476647558659373206291635324768958432433509563104347017837885763365758
#               * u), QuadExtField(1985150602287291935568054521177171638300868978215655730859378665066344726373823718423869104263333984641494340347905
#                                  + 927553665492332455747201965776037880757740193453592970025027978793976877002675564980949289727957565575433344219582
#                                  * u))
# , tau_in_g2: (QuadExtField(186544079744757791750913777923182116923406997981176124505869835669370349308168084101869919858020293159217147453183
#                            + 2680951345815209329447762511030627858997446358927866220189443219836425021933771668894483091748402109907600527683136
#                            * u),
#               QuadExtField(2902268288386460594512721059125470579172313681349425350948444194000638363935297586336373516015117406788334505343385
#                            + 1813420068648567014729235095042931383392721750833188405957278380281750025472382039431377469634297470981522036543739

#fixed
g1_points=(3685416753713387016781088315183077757961620795782546409894578378688607592378376318836054947676345821548104185464507, 1339506544944476473020471379941921221584933875938349620426543736416511423956333506472724655353366534992391756441569)

#fixed
g2_points_affine=[(352701069587466618187139116011060144890029952792775240219908644239793785735715026873347600343865175952761926303160,
                    3059144344244213709971259814753781636986470325476647558659373206291635324768958432433509563104347017837885763365758)
                   ,(1985150602287291935568054521177171638300868978215655730859378665066344726373823718423869104263333984641494340347905,
                     927553665492332455747201965776037880757740193453592970025027978793976877002675564980949289727957565575433344219582)
                   , (186544079744757791750913777923182116923406997981176124505869835669370349308168084101869919858020293159217147453183,
                        2680951345815209329447762511030627858997446358927866220189443219836425021933771668894483091748402109907600527683136)
                    ,(2902268288386460594512721059125470579172313681349425350948444194000638363935297586336373516015117406788334505343385,
                      1813420068648567014729235095042931383392721750833188405957278380281750025472382039431377469634297470981522036543739)]
#fixed
g2_points_affine=[(y,x) for (x,y) in g2_points_affine]

#variable
fixed_column_commitments=[to_int(C_px_nm), to_int(C_py_nm), to_int(C_s_nm)] # px, py, s commitments

print("FIxed_columns:", fixed_column_commitments)
#1
verifier_key={'g1':g1_points,
              'g2':g2_points_affine,
              'commitments':fixed_column_commitments} #g1(one pt(x,y)) , g2[(x,y)..(xn,yn), fc_commitments]

#2
cnd_add_res= Result_point

#3
witness_commitments=[to_int(C_b_v_nm), to_int(C_acc_ip_nm), to_int( C_acc_x_nm), to_int(C_acc_y_nm)] #b, accip, accx, accy
#
# EXPECTED_ALPHA = [23426295910140870709614097412433960347746242342772840884066757906985100343590,
#                   46433544455077235545632682909406958794646428824021350807274305193686650751236,
#                   78101732610314093593150729898315267434854171850795179589607409285815531790,
#                   593197255987830876876009860956149019051956889376694517098490195230307214182,
#                   32175196951432882449291708537928919219460156628583290699727577517487325664113,
#                   34948741935357743784650851171470586551760506493489743006361967647813201562252,
#                   48766446903835583133423634840534770408834461876682423474505157724475361584745]


class Transcript:
    def __init__(self, modulus: int, initial: bytes):
        self.modulus = modulus
        self._shake = hashlib.shake_128()
        self._length = None
        self.label(initial)

    def separate(self):
        if self._length is not None:
            self._shake.update(struct.pack(">I", self._length))
        self._length = None

    def write(self, data: bytes):
        if self._length is None:
            self._length = 0
        self._shake.update(data)
        self._length += len(data)

    def write_bytes(self, data: bytes):
        """
        Write `data` into the transcript, breaking into <=2^31-1 chunks
        and inserting length-footers between them.
        """
        HIGH = 1 << 31
        idx = 0
        total_len = len(data)
        while idx < total_len:
            # Initialize or fetch the byte-counter since last separator
            if self._length is None:
                self._length = 0
            # How many bytes can we consume before hitting (2^31-1)
            remaining_allowed = (HIGH - 1) - self._length
            to_take = min(remaining_allowed, total_len - idx)

            # Absorb that slice
            chunk = data[idx: idx + to_take]
            self.write(chunk)

            # Advance
            idx += to_take

            # If we're done, exit
            if idx >= total_len:
                return

            # Otherwise we hit the chunk-size limit: set the MSB flag
            self._length |= HIGH

            # Emit a separator and loop for the rest
            self.separate()

    def label(self, lbl: bytes):
        self.separate()
        self.write(lbl)
        self.separate()

    def challenge(self, label: bytes) -> int:
        self.label(label)
        self.write(b"challenge")
        ret = self.read_reduce()
        self.separate()
        return ret

    def _read_xof(self, n: int) -> bytes:
        shake_copy = self._shake.copy()
        return shake_copy.digest(n)

    def append(self, data):
        self.separate()
        self.write_bytes(data)
        self.separate()

    def add_serialized(self, label: bytes, data):
        self.label(label)
        self.append(data)

    def read_reduce(self) -> int:
        # (bitlen(p) + 128 + 7) // 8 bytes
        n = math.ceil((self.modulus.bit_length() + 128) / 8)
        rnd = self._read_xof(n)
        # reverse for BE→LE
        val = int.from_bytes(rnd[::-1], "little")
        return val % self.modulus

    def get_constraints_aggregation_coeffs(self, n):
        out = []
        for _ in range(n):
            out.append(self.challenge(b"constraints_aggregation"))
        return out

    def get_evaluation_point(self,n=1):
        out =list()
        out.append(self.challenge(b"evaluation_point"))
        return out

    def get_kzg_aggregation_challenges(self,n):
        out=[]
        for _ in range(n):
            out.append(self.challenge(b"kzg_aggregation"))
        return out


    def serialize_object(self, obj: Any) -> bytes:
        """Serialize different types of objects to bytes"""
        if isinstance(obj, int):
            byte_len = (obj.bit_length() + 7) // 8
            if byte_len <= 32:
                return obj.to_bytes(32, 'little')
            elif byte_len <= 48:
                return obj.to_bytes(48, 'big')
            else:
                raise ValueError("Integer too large to serialize in 48 bytes")

        elif isinstance(obj, tuple):
            if len(obj) == 2 and (obj[0].bit_length()//8 + obj[1].bit_length()//8) > 64:
                # G1 point (x, y) where both are integers
                x, y = obj
                return self.serialize_object(x) + self.serialize_object(y)
            else:
                x,y=obj
                # Uncompressed: serialize x, y, and flag
                flag = b'\x80' if y > (S_PRIME - 1) // 2 else b'\x00'
                return self.serialize_object(x) + self.serialize_object(y) + flag

        elif isinstance(obj, list):
            # List of items
            result = b""
            for item in obj:
                result += self.serialize_object(item)
            return result

        elif isinstance(obj, dict):
            # Handle dictionary (like verifier key)
            result = b""
            if 'g1' in obj and 'g2' in obj:
                # Serialize verifier key

                result += self.serialize_object(obj['g1'])  # G1 point
                # Handle g2 as a list
                g2_list = obj['g2']

                for g2_item in g2_list:
                    result += self.serialize_object(g2_item)

                # Add commitments if present
            if 'commitments' in obj:
                commitments = obj['commitments']
                for commitment in commitments:
                    result += self.serialize_object(commitment)

            return result
        elif isinstance(obj, bytes):
            return obj
        else:
            raise TypeError(f"Unsupported object type for serialization: {type(obj)}")



#Intitialize the Transcript
t1 = Transcript(S_PRIME, b"Bandersnatch_SHA-512_ELL2")
t1.add_serialized( b"vk",t1.serialize_object(verifier_key))
t1.add_serialized(b"instance", t1.serialize_object(cnd_add_res))

#For alphas
t1.add_serialized(b"committed_cols", t1.serialize_object(witness_commitments))

alphas = t1.get_constraints_aggregation_coeffs(7)

print("ALPHAS_GOT:", alphas)

#For Evaluation point Zeta
C_q_commitment= (159577665654184642528445061443139058506304804968976952286485779705426937078646573618472846402373487691792682308110, 736587099163428816505841914367133800750653852217851995337945991731846846996489113799578870214787258948989745666943)\

C_q_bytes=t1.serialize_object(C_q_commitment)
# print("C_q_bytes:", C_q_bytes)

t1.add_serialized(b"quotient", C_q_bytes)

zeta=t1.get_evaluation_point(1)
# print("zeta", zeta)

#for v_vector challenges
P_x_zeta= 47343875990584331598405967528753366118614278134592011183134266696788905735943
P_y_zeta= 24216913497027158992623275006635750309984928064929829679306593885849688290425
s_zeta= 29322573334654311120001711370531424403351172520016761183738197922897588434582
b_zeta= 803668754527118197032699045453825514185212976018444075862755526783455647586
acip_zeta= 37590886240661730597364636477866907788765220356502722654351659246520208605795
acc_x_zeta= 30949462086139024225853848904744182973428625667398141975923126676486178430393
acc_y_zeta= 46315719240210991676423362516277234398874681322268445241088393795660974665486
L_Zeta_omega=30621163303482757449119987082971412951766100870193575818832275238009455772101

evals= t1.serialize_object(P_x_zeta)+ t1.serialize_object(P_y_zeta)+ t1.serialize_object(s_zeta)+ t1.serialize_object(b_zeta)+t1.serialize_object(acip_zeta)+t1.serialize_object(acc_x_zeta)+ t1.serialize_object(acc_y_zeta)
t1.add_serialized(b"register_evaluations", evals)

linearized_evals=t1.serialize_object(L_Zeta_omega)
t1.add_serialized(b"shifted_linearization_evaluation", linearized_evals)

cf_vectors=t1.get_kzg_aggregation_challenges(8)

# print("vectors:",cf_vectors)
# print(f"\nalphas: {alphas} \n\nEXPECTED_ALPHA: {EXPECTED_ALPHA}")

