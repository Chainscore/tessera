import asyncio
import json
from time import time
import pytest
import os
from tsrkit_types import U32
from jam.log_setup import node_logger as logger
from jam.utils.constants import GENESIS_TS
from jam.storage.da.mappings import (
    PackageSegmentMap,
    SegmentErasureMap,
)
from tests.unit.audit.types import AuditVector, AuditVectors
from tests.integration.utils.setup_processes import Client, Role, setup_processes


import os
import json


CLIENTS = [
    Client(Role.VAL, 40000, theme="cyberpunk"),
    Client(Role.VAL, 40001, theme="monokai"),
    Client(Role.VAL, 40002, theme="noir"),
    Client(Role.VAL, 40003, theme="sunset"),
    Client(Role.VAL, 40004, theme="gruvbox"),
    Client(Role.VAL, 40005, theme="dracula"),
    Client(Role.BUILDER, 40006, theme="nord"),
]

async def node_task():

    # Folder path
    folder_path = "/home/dikshant441/Desktop/jam/forks-test"

    # Loop through files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):  # Only read .json files
            file_path = os.path.join(folder_path, filename)
            print(f"Reading file: {file_path}")

            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    print("✅ Successfully loaded JSON")
                    # do something with `data`
                    # e.g., print(data.keys()) or process it
            except Exception as e:
                print(f"❌ Error reading {filename}: {e}")


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_auditor():
    await setup_processes(CLIENTS, [node_task], 30)
