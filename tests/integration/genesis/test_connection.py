import asyncio
import pytest
from jam.__main__ import main

@pytest.mark.asyncio
async def test_connection():
    print("test_connection")
    client1 = asyncio.create_task(main(name="Alice", genesis_path="genesis.json", db_path="db/30333", port=30333, start_genesis=True, theme="polkadot"))
    client2 = asyncio.create_task(main(name="Bob", genesis_path="genesis.json", db_path="db/30334", port=30334, start_genesis=True, theme="matrix"))

    await client1
    await client2
    
    print("test_connection done")
