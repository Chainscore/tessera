import pickle
from typing import Dict, Optional
from aioquic.tls import SessionTicket

class SessionTicketStore:
    def __init__(self, node_name) -> None:
        """Initialize the session ticket store and load existing tickets from file."""
        self.file = f"seeds/{node_name}/session_tickets.pkl"
        self.tickets: Dict[bytes, SessionTicket] = self.load_tickets()

    def add(self, ticket: SessionTicket) -> None:
        """Store a QUIC session ticket and save to file."""
        self.tickets[ticket.ticket] = ticket
        self.save_tickets()

    def pop(self, label: bytes) -> Optional[SessionTicket]:
        """Retrieve and remove a stored session ticket, then save changes."""
        ticket = self.tickets.pop(label, None)
        self.save_tickets()
        return ticket

    def save_tickets(self) -> None:
        """Save all session tickets to a file."""
        with open(self.file, "wb") as f:
            pickle.dump(self.tickets, f)

    def load_tickets(self) -> Dict[bytes, SessionTicket]:
        """Load session tickets from file if it exists."""
        try:
            with open(self.file, "rb") as f:
                return pickle.load(f)
        except (FileNotFoundError, EOFError):
            return {}  # Return an empty dictionary if the file doesn't exist or is empty

def read_store(port: int):
    with open(f"seeds/{port}/session_tickets.pkl", "rb") as file:
        data = pickle.load(file)
    print(type(data))
    print((data))
