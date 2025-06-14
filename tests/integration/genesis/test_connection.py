import asyncio
import os
import pytest

clients = [40000, 40001,
    # ("charlie", 40002),
    # ("dave", 40003),
    # ("eve", 40004),
    # ("frank", 40005),
]


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_connection():
    tasks = []
    from jam.__main__ import main
    for client in clients:
        tasks.append(
            main(
                genesis_path="dev-spec.json",
                db_path=f"db/{client}",
                env=f"envs/{client}.env",
                start_genesis=True,
                theme="matrix",
                is_builder=False,
                is_validator=True,
            )
        )

    await asyncio.gather(*tasks)
