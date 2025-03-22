
class Peer:
    """
    Represents a peer in the network
    Args:
        host (str): Hostname of the peer
        port (int): Port number of the peer
        san (str): Subject Alternative Name of the peer
    """
    host: str
    port: int
    san: str

    def __init__(self, host: str, port: int, san: str):
        self.host = host
        self.port = port
        self.san = san