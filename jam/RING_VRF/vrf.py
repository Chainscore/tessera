
from typing import  Tuple,List,Dict
from jam.ring_vrf.curve.point import Point
from jam.ring_vrf.curve.curve import Curve
from jam.types.protocol.crypto import Hash

class VRF(Curve):

    curve: Curve
    
    def generate_nonce(self, secret_key: int, input_point: Point) -> int:
        """Generate a nonce modulo the curve's order"""
        # Stage 1: Hash the secret key in little-endian
        sk_encoded = secret_key.to_bytes(32, 'little')
        hashed_sk = bytes(Hash.sha512(sk_encoded))
        sk_hash = hashed_sk[32:64]  # Use second half of the SHA-512 output

        
        # Stage 2: Concatenate the hashed key and input point's octet string
        point_octet = input_point.point_to_string()
        data = sk_hash + point_octet
        
        # Stage 3: Hash the concatenated data
        nonce_hash = bytes(Hash.sha512(data))
        
        # Stage 4: Interpret the hash as a little-endian integer
        nonce = int.from_bytes(nonce_hash, 'little')
        
        # Reduce nonce modulo the curve's order to ensure it's within range
        return nonce % self.curve.ORDER

    def challenge(self, Y: Point, I: Point, O: Point, U: Point, V: Point, ad: bytes) -> int:
        """Produce the challenge scalar c"""
        # Step 1: Create the initial string with the suite ID and version
        str0 = self.curve.SUITE_STRING.encode() + bytes([0x02])
        # Step 2: Concatenate the input points into strn
        strn = str0
        for P in [Y, I, O, U, V]:
            strn += P.point_to_string()  # Converts point to compressed octet string
        
        # Step 3: Hash strn || ad || 0x00 to generate the hash
        hash_input = strn + ad + bytes([0x00])
        h = bytes(Hash.sha512(hash_input))[:32]

        # Step 4: Interpret the first 32 bytes as a little-endian integer
        c = int.from_bytes(h, 'big') % self.curve.ORDER

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

