from typing import Any, Tuple
from jam.ring_vrf.ring_proof.pcs_raw_vk import g1_points, g2_points


fixed_column_commitments=[(2184322408700443054740347828385756395887450499544961458434449967515585230119811422303998494678625856593099009354269, 621275079380005050148034176492155566905504849318972088470262599112846758633822504165123387322379379707917835693572)
 ,(2222889968827206885680289387487836215699680640435571691849910457746642206407839358287853588403334593295834133157025, 3775467963124612154874263095238481633395061438101857405422420054510930838229011019841213453476026844481467689115510)
 ,(2908850075820590559825558591796489926137468891350244723135070577033834833074699096095104618216690855741912718144719, 436343574607707198583869582232412021753441754571435491281710311907340647898134029725340232367691953082908705963261)
] # px, py, s commitments


#1
verifier_key={'g1':g1_points,
              'g2':g2_points,
              'commitments':fixed_column_commitments} #g1(one pt(x,y)) , g2[(x,y)..(xn,yn), fc_commitments]

#2
cnd_add_res=(44648389602443941246322372236520302377738843362627918945068618001357248615438,
30442058788205120169111780157211650520166686827644460980327172006316630237607)

#3
witness_commitments=[(1332310689855977281988073361583473861448181703578082464893324255082586328540004758008760342419545320465710360446231,
                       1083094159812582322688886646243817038393280166989720523735466912565067215129958786830520140761135404613535398368005),
                      (2621192239526746493690276760363672663454509538346148804895722177661106008210052886974309467617179955564514764053725,
                       1132756997463485914985424635482244867407668321196232613772498458907825975896958220234840325938268628831098913606929),
                      (208517810521014456969594821902236745146650230125672150449544355893015815481257798374873866369450527071881310158626,
                       3880149744675340773693842704377702960563691427832818693891594250964317384604403130285779991132012905121890796337854),
                      (2099484474692952046119311146814746722623650964260983548272397559530954731156540861451355986202655309318717421274032,
                       608054885751253195670196163882239137920749686204297379566519172189040854866614063627708313340299408889892231573333)] #b, accip, accx, accy

#update

#digest

#transcript  -start with empty transcript

#add verifier key to transcript - label: 'vk'

#add the piop result - conditional_addition_result - label:'instance'

#add the wittness commitments - label:'committed_cols'

# get the alphas - label: 'constraints_aggregation' n=7

from hashlib import shake_128

class Transcript:
    def __init__(self):
        self.buffer = bytearray()
        self.last_pos = 0

    # add the label
    def add_label(self, label: Any):
        self.separator()
        self.buffer += label
        self.separator()

    # add the data
    def add_data(self, data: Any):
        self.separator()
        self.buffer += self.serialize_object(data)
        self.separator()

    #add serialize
    def add_serialized(self, label: bytes, data: Any):
        self.add_label(label)
        self.add_data(data)

    #implement the seperator
    def separator(self):
        length = len(self.buffer) - self.last_pos
        self.last_pos = len(self.buffer)
        self.buffer += length.to_bytes(4, 'big')


    #get the chalenge
    def get_challenge(self, label: bytes, num_bytes=32) -> bytes:
        tmp = self.buffer.copy()
        length = len(tmp)
        tmp += (len(tmp) - 0).to_bytes(4, 'big')
        tmp += label
        tmp += (len(tmp) - length).to_bytes(4, 'big')
        tmp += b"challenge"

        hasher = shake_128()
        hasher.update(tmp)
        return hasher.digest(num_bytes)


    #converting the input object to string
    def serialize_object(self, obj: Any) -> bytes:
        """Serialize different types of objects to bytes"""
        if isinstance(obj, int):
            # Serialize as a 64-bit big-endian integer
            return obj.to_bytes(48, byteorder='big')

        elif isinstance(obj, tuple):
            if len(obj) == 2 and all(isinstance(x, int) for x in obj):
                # G1 point (x, y) where both are integers
                x, y = obj
                return self.serialize_object(x) + self.serialize_object(y)

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
            elif 'commitments' in obj:
                commitments = obj['commitments']
                for commitment in commitments:
                    result += self.serialize_object(commitment)

            return result
        elif isinstance(obj, bytes):
            return obj
        else:
            raise TypeError(f"Unsupported object type for serialization: {type(obj)}")


# Initialize the transcript
t = Transcript()

# Add fake verifier key
t.add_serialized(b"vk", verifier_key)

t.add_serialized(b"instance", cnd_add_res)

t.add_serialized(b'commited_cols', witness_commitments)

alpha = t.get_challenge(b"constraints_aggregation",224)

alphas=[]
start=0
end=32
for i in range(7):
    alphas.append(alpha[start:end])
    start=end
    end=end+32
alphas=[int.from_bytes(each, 'big') for each in alphas]

for i in range(len(alphas)):
    print(f"Alpha {i}: {alphas[i]}")


Expected_Alphas = [23426295910140870709614097412433960347746242342772840884066757906985100343590,
                       46433544455077235545632682909406958794646428824021350807274305193686650751236,
                       78101732610314093593150729898315267434854171850795179589607409285815531790,
                       593197255987830876876009860956149019051956889376694517098490195230307214182,
                       32175196951432882449291708537928919219460156628583290699727577517487325664113,
                       34948741935357743784650851171470586551760506493489743006361967647813201562252,
                       48766446903835583133423634840534770408834461876682423474505157724475361584745]

for i in range(len(alphas)):
    print(alphas[i]==Expected_Alphas)





























