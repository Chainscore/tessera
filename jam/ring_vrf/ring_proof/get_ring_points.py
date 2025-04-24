from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint
from jam.ring_vrf.ring_proof.constants import Max_ring_size, PaddingPoint
from jam.ring_vrf.ring_proof.short_weierstrass import twisted_edward_to_sw, is_on_weierstrass

# secret_t= 744680505869196983594822479191902629615519705971981518975526000476936615681 #vector 1
import time

st=time.time()

secret_t=5763201215905959162196757845174861855612849471748236070748880108968682793542 #vect 7
secret_t_little=0x66a31ab3317c04a30455d4023e8265ec06c3303c94d560b959d4e024f527d0577f
secret_t_l=int(bin(secret_t)[2:][::-1],2)
block_producer="b0e1f208f9d6e5b310b92014ea7ef3011e649dab038804759f3766e01029d623"
pk_ring="7b32d917d5aa771d493c47b0e096886827cd056c82dbdba19e60baa8b2c60313d3b1bdb321123449c6e89d310bc6b7f654315eb471c84778353ce08b951ad471561fdb0dcfb8bd443718b942f82fe717238cbcf8d12b8d22861c8a09a984a3c5b0e1f208f9d6e5b310b92014ea7ef3011e649dab038804759f3766e01029d6234fd11f89c2a1aaefe856bb1c5d4a1fad73f4de5e41804ca2c17ba26d6e10050c86d06ee2c70da6cf2da2a828d8a9d8ef755ad6e580e838359a10accb086ae437ad6fdeda0dde0a57c51d3226b87e3795e6474393772da46101fd597fbd456c1b3f9dc0c4f67f207974123830c2d66988fb3fb44becbbba5a64143f376edc51d9"
pk_list=[]
pk_x_y_list=[]
pk_x_list=[]
frm=0
to=64


# print(len(pk_ring))

for i in range(len(pk_ring)//64):
    pk_list.append(pk_ring[frm:to])
    frm=to
    to+=64

# print("PK",pk_list)
sample="355788aa5f7bdf89352c957833b217c025a43f96ec996d0f4c5f90cab6457f1e"
# print(len(sample))

count=0
for string in pk_list:
    try:
        pk=BandersnatchPoint.string_to_point(string)
        pk_x_y_list.append(twisted_edward_to_sw((pk.x, pk.y)))
        # print(twisted_edward_to_sw((pk.x,pk.y)))
        # print(pk)
        pk_x_list.append(pk.x)
        # print(pk.is_on_curve())

    except ValueError as e:
        count+=1
# print("Pk str list",pk_list)
# print("p_x_y_list",pk_x_y_list)
# print(count)
end=time.time()

def main():
    print("PK_STRINGS")
    print('b_p in pk_list:',block_producer in pk_list, pk_list.index(block_producer))

if __name__=="__main__":
    main()
# print(end-st)
