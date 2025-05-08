import math
import hashlib, struct
from typing import Any
from jam.ring_vrf.ring_proof.constants import S_PRIME
from jam.ring_vrf.ring_proof.helpers import bls_g1_compress
from typing import Any, Tuple
from py_ecc.bls12_381 import curve_order

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


fixed_column_commitments=[(2184322408700443054740347828385756395887450499544961458434449967515585230119811422303998494678625856593099009354269, 621275079380005050148034176492155566905504849318972088470262599112846758633822504165123387322379379707917835693572)
 ,(2222889968827206885680289387487836215699680640435571691849910457746642206407839358287853588403334593295834133157025, 3775467963124612154874263095238481633395061438101857405422420054510930838229011019841213453476026844481467689115510)
 ,(2908850075820590559825558591796489926137468891350244723135070577033834833074699096095104618216690855741912718144719, 436343574607707198583869582232412021753441754571435491281710311907340647898134029725340232367691953082908705963261)
] # px, py, s commitments
g1_points=(3685416753713387016781088315183077757961620795782546409894578378688607592378376318836054947676345821548104185464507, 1339506544944476473020471379941921221584933875938349620426543736416511423956333506472724655353366534992391756441569)

g2_points_affine=[(352701069587466618187139116011060144890029952792775240219908644239793785735715026873347600343865175952761926303160,
                    3059144344244213709971259814753781636986470325476647558659373206291635324768958432433509563104347017837885763365758)
                   ,(1985150602287291935568054521177171638300868978215655730859378665066344726373823718423869104263333984641494340347905,
                     927553665492332455747201965776037880757740193453592970025027978793976877002675564980949289727957565575433344219582)
                   , (186544079744757791750913777923182116923406997981176124505869835669370349308168084101869919858020293159217147453183,
                        2680951345815209329447762511030627858997446358927866220189443219836425021933771668894483091748402109907600527683136)
                    ,(2902268288386460594512721059125470579172313681349425350948444194000638363935297586336373516015117406788334505343385,
                      1813420068648567014729235095042931383392721750833188405957278380281750025472382039431377469634297470981522036543739)]

g2_points_affine=[(y,x) for (x,y) in g2_points_affine]

#1
verifier_key={'g1':g1_points,
              'g2':g2_points_affine,
              'commitments':fixed_column_commitments} #g1(one pt(x,y)) , g2[(x,y)..(xn,yn), fc_commitments]

#2
cnd_add_res=(2710605788098020115969868248537441665859558254081583689800100488017991893059, 38942065359286004884825904391036291403783556903118477722228967817717281647437)

#3
witness_commitments=[(1332310689855977281988073361583473861448181703578082464893324255082586328540004758008760342419545320465710360446231,
                       1083094159812582322688886646243817038393280166989720523735466912565067215129958786830520140761135404613535398368005),
                      (2621192239526746493690276760363672663454509538346148804895722177661106008210052886974309467617179955564514764053725,
                       1132756997463485914985424635482244867407668321196232613772498458907825975896958220234840325938268628831098913606929),
                      (208517810521014456969594821902236745146650230125672150449544355893015815481257798374873866369450527071881310158626,
                       3880149744675340773693842704377702960563691427832818693891594250964317384604403130285779991132012905121890796337854),
                      (2099484474692952046119311146814746722623650964260983548272397559530954731156540861451355986202655309318717421274032,
                       608054885751253195670196163882239137920749686204297379566519172189040854866614063627708313340299408889892231573333)] #b, accip, accx, accy

EXPECTED_ALPHA = [23426295910140870709614097412433960347746242342772840884066757906985100343590,
                  46433544455077235545632682909406958794646428824021350807274305193686650751236,
                  78101732610314093593150729898315267434854171850795179589607409285815531790,
                  593197255987830876876009860956149019051956889376694517098490195230307214182,
                  32175196951432882449291708537928919219460156628583290699727577517487325664113,
                  34948741935357743784650851171470586551760506493489743006361967647813201562252,
                  48766446903835583133423634840534770408834461876682423474505157724475361584745]


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
                flag=int(128).to_bytes(1, 'little')
                if y >(S_PRIME-1)//2:
                    return self.serialize_object(x) + self.serialize_object(y)+flag

                return self.serialize_object(x)+ self.serialize_object(y)


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

alphas = t1.get_constraints_aggregation_coeffs(len(EXPECTED_ALPHA))

#For Evaluation point Zeta
C_q_commitment=(2549617373447607513991960595997283247309914767560258740520327486362563366281642266428195629369789554374774378038686,
 2533053437940829391551014576321233915087611078555948078165800094261952712805435708755714584312615895714192869980011)

C_q_bytes=t1.serialize_object(C_q_commitment)
# print("C_q_bytes:", C_q_bytes)

t1.add_serialized(b"quotient", C_q_bytes)

zeta=t1.get_evaluation_point(1)
# print("zeta", zeta)

#for v_vector challenges

P_x_zeta =51661965445089587819320049751583786375164447966727445464203134654815915588661
P_y_zeta= 37677903892786504698626961257993799069550081708377744789604954646604979928172
s_zeta= 31830864498423299983513330344445285252604438446220124847358647029236256819548
b_zeta= 2862392824402782508413951591912393597556229147964652793866091017499021712351
acip_zeta=3687942561837054344693651945369831752849919356025525195242591992348029951548
acc_x_zeta= 7914979119298103019530467201196476028021784095563860206196072523175263701020
acc_y_zeta= 30713297100934553101812845767340019317731271289940620926880944610066654978333
L_Zeta_omega= 49499219101665281774193159448437049075993807294762252099097581130130875122570


evals= t1.serialize_object(P_x_zeta)+ t1.serialize_object(P_y_zeta)+ t1.serialize_object(s_zeta)+ t1.serialize_object(b_zeta)+t1.serialize_object(acip_zeta)+t1.serialize_object(acc_x_zeta)+ t1.serialize_object(acc_y_zeta)
t1.add_serialized(b"register_evaluations", evals)

linearized_evals=t1.serialize_object(L_Zeta_omega)
t1.add_serialized(b"shifted_linearization_evaluation", linearized_evals)

cf_vectors=t1.get_kzg_aggregation_challenges(8)

# print("vectors:",cf_vectors)
# print(f"\nalphas: {alphas} \n\nEXPECTED_ALPHA: {EXPECTED_ALPHA}")

