
from typing import  Tuple,List,Dict
from jam.RING_VRF.curve.point import Point
from jam.RING_VRF.curve.curve import Curve
from jam.utils.conv_helper import ConversionHelper


class VRF(Curve):

    curve: Curve
    @staticmethod
    def generate_nonce(secret_key: int, input_point: Tuple[int, int]) -> int:
        """Generate a nonce"""

        hashed_sk_string = ConversionHelper.to_int(secret_key.to_bytes(32, 'little'))
        # print("sk_str",secret_key.to_bytes(32,'little').hex())
        # print(hashed_sk[32:])
        h_string = Point.point_to_string(input_point)
        # print(h_input)
        k_string = ConversionHelper.to_hash(hashed_sk_string[32:63] + hashed_sk_string)
        # print(Utilities.string_to_int(k_string)>constants.ORDER)
        return ConversionHelper.to_int(k_string)


    @staticmethod
    def challenge(Y: Tuple[int, int], I: Tuple[int, int], O: Tuple[int, int], U: Tuple[int, int],
                  V: Tuple[int, int], ad: bytes) -> int:
        str_0 = VRF.curve.SUITE_STRING.encode() + bytes([0x02])
        # Step 2: Concatenate the input points in sequence using point_to_string
        points = [Y, I, O, U, V]
        str_n = str_0
        for P in points:
            # print(Elligator2.check_is_point(P[0],P[1]))
            str_n += Point.point_to_string(P)
        # Step 3: Append additional data and termination byte
        h = ConversionHelper.to_hash(str_n + ad + bytes([0x00]))
        # Step 5: Convert hash to challenge scalar
        # Use first 32 bytes
        c = ConversionHelper.to_int(bytes(h[:32]))
        return c

    def proof(self, *arg):
        ...



    def verify(self, *arg):
        ...


    @staticmethod
    def select_winning_ticket(tickets: List[Dict]) -> Tuple[List[Dict], Dict]:

        valid_tickets = [ticket for ticket in tickets if ticket['valid']]
        if not valid_tickets:
            return [], None

        winning_ticket = min(valid_tickets, key=lambda ticket: ticket['output_point'])
        return valid_tickets, winning_ticket

