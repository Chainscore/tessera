import asyncio
import os
import sys

# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

from jam.operations import operate
from tests.integration.utils.setup_processes import Client, Role, setup_processes

async def main():
    print("Starting 6-node local network...")
    CLIENTS = [
        Client(Role.VAL, 40000 + 0),
        Client(Role.VAL, 40000 + 1),
        Client(Role.VAL, 40000 + 2),
        Client(Role.VAL, 40000 + 3),
        Client(Role.VAL, 40000 + 4),
        Client(Role.VAL, 40000 + 5),
    ]
    
    # Run for 1 hour
    await setup_processes(CLIENTS, [operate], 3600, rpc_flag=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Network stopped by user.")
