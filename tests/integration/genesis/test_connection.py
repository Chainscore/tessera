import asyncio
import os
import pytest
clients = [
    ("Alice", 30333),
    ("Bob", 30334),
    ("Carol", 30335),
    ("Dave", 30336),
    ("Eve", 30337),
    ("Frank", 30338),
]


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_connection():
    tasks = []
    from jam.__main__ import main
    for client in clients:
        tasks.append(
            main(
                name=client[0],
                genesis_path="genesis.json",
                db_path=f"db/{client[1]}",
                port=client[1],
                start_genesis=True,
                theme="matrix",
                is_builder=False,
                is_validator=True,
            )
        )

    await asyncio.gather(*tasks)
