import json
import pytest
import os
import shutil
import tempfile
from enum import Enum
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union, Literal
from jam.db.kv import KVStore
from jam.state.state import State
from jam.network.peer import Peer
from jam.consensus.safrole.safrole import Safrole
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic, Ed25519Public
from jam.types.protocol.core import ServiceId,BlobLength
from jam.types.base.sequences.bytes.bytes import Bytes

# Initialize FastAPI with metadata for Swagger UI
app = FastAPI(
    title="Tessera RPC API",
    description="RPC for Tessera node ",
    version="1.0.0",
)


db_path = tempfile.mkdtemp()
   
# print(db_path)
# Initialize store
kv = KVStore(db_path)
   
# State checking:
    
peerlist = json.load(open("../../genesis.json"))["peers"]
peers = [Peer(port=pr["port"], host=pr["host"], san=pr["id"]) for pr in peerlist]
validators = [ValidatorData(
bandersnatch=BandersnatchPublic(pr["bandersnatch_public"]),
ed25519=Ed25519Public(pr["ed25519_public"]),
bls=BlsPublic(pr["bls_public"]), metadata=ValidatorMetadata(bytes(128)) ) for pr in peerlist]
state = State.genesis(validators, Safrole.arrange_fallback(ByteArray32(bytes(32)), validators))
state.save(kv)

print(state.load(kv).phi)

# Following the etherum json rpc api structure
"""
curl https://docs-demo.quiknode.pro/ \
  -X POST \
  -H "Content-Type: application/json" \
  --data '{"method":"eth_getStorageAt","params":["0xc98F11DAAAC76D3ef368fDF54fbbA34FfD951976", "0x2293", "latest"],"id":1,"jsonrpc":"2.0"}'

{"jsonrpc":"2.0","id":1,"result":"0x0000000000000000000000000000000000000000000000000000000000000000"}

"""

# Request model
class RpcRequest(BaseModel):
    method: str
    jsonrpc: str 
    params: Dict[str, Any]
    id: Optional[Any]

# Response models
class RpcResponse(BaseModel):
    jsonrpc: str
    result: Any = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[int]


@app.post("/rpc.tessera", response_model=RpcRequest)
async def rpc_handler(request: RpcRequest):
    """
    RPC requests for different methods.
    """
    method = request.method
    params = request.params

    if method == "stateRoot":
        # Handle stateRoot method
        state_root = state.load(kv)
        if len(request.params) != 1:
            return RPCResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected header_hash"},
            )
        
        # Extract header_hash from params
        header_hash = request.params.get("Hash")

        # Validate header_hash
        if len(header_hash) != 32:
            return RPCResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected header_hash"},
            )

        # Fetch latest state from db
        db_state = state.load(kv).phi

        # Return the state root
        if(header_hash == db_state.header_hash):
            return RPCResponse(
                jsonrpc="2.0",
                id=request.id,
                result=db_state.state_root,
            )
        else:
            return RPCResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )
    elif method == "getBlock":

        # TODO: CHECK THISSS 
        # Handle getBlock method
        if len(request.params) != 1:
            return RPCResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected block_hash"},
            )
        
        # Extract block_hash from params
        block_hash = request.params.get("Hash")

        # Validate block_hash
        if len(block_hash) != 32:
            return RPCResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected block_hash"},
            )

        # Fetch latest state from db
        db_state = state.load(kv).phi

        # Return the block
        if(block_hash == db_state.block_hash):
            return RPCResponse(
                jsonrpc="2.0",
                id=request.id,
                result=db_state.block,
            )
        else:
            return RPCResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )
        

