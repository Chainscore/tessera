from numpy import block
from quart import jsonify
from jam.consensus.grandpa.finality import Finality
from jam.state.merkle.merkle import StateTrie
from jam.state.state import state
from jam.types.block import Block
from jam.types.header import Header
from jam.types import  U32
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.state.accounts import  StorageView, PreImageView, TimestampsView
from jam.types.state.delta import LookupTable

def best_block_handler(params, request_id, db):

    #fetch the latest updated state and load block using its time slot
    from jam.state.state import state as updated_state
    block = Block.load(updated_state.tau, db)

    if len(params) != 0:
            raise ValueError("Invalid parameters: expected no params")
    return [Header.__hash__(block.header), int(block.header.slot)]

def finalized_block_handler(params, request_id, db):
    if len(params) != 0:
            return jsonify({
                "jsonrpc":"2.0",
                "id":request_id,
                "error":{"code": -32602, "message": "Invalid parameters: expected no params"},
                })
    final = Finality.load_final(db)
    return [Header.__hash__(final.header), int(final.header.slot)]

def parent_block_handler(params, request_id, db):
    #fetch the latest updated state and load block using its time slot
    from jam.state.state import state as updated_state
    block = Block.load(updated_state.tau, db)
    print("blupdated_stateock", updated_state.tau)
    if len(params) != 1:
            return jsonify({
                "jsonrpc":"2.0",
                "id":request_id,
                "error":{
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            }
            )   
    
    if len(params):
            ## condition if the time slot is of genesis block
        if block.header.slot == U32(0):
            return jsonify({
                    "jsonrpc":"2.0",
                    "id":request_id,
                    "error":{
                    "code": -32602,
                    "message": "No parent block available for genesis block"},
                }
                )

            ## using state trie function
            ## TODO: Make a rocksdb search function that will fetch block with needed hash. As of now returning current state
        if bytes(params["Hash"]):
                # Return the parent block
                parent_block = block.load_parent(block.header.slot, db)
                print("parent_block api",parent_block)
                return [ Header.__hash__(parent_block.header), int(parent_block.header.slot) ]

def state_root_handler(params, request_id, db):
    if len(params) != 1:
        return jsonify({
                "jsonrpc":"2.0",
                "id":request_id,
                "error":{
                    "code": -32602,
                    "message": "Invalid parameters: expected  one params",
                },
            }
            )

    header_hash = params.get("Hash")
    if header_hash is None or len(header_hash) != 32:
        return jsonify({
                "jsonrpc":"2.0",
                "id":request_id,
                "error":{
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            }
            )
    
    # TODO: Make a rocksmain_db search function that will fetch block with needed hash. As of now returning current state
    if bytes(params["Hash"]):
        return [
            StateTrie.root_hash
        ]
    else:
        return jsonify({
            "jsonrpc":"2.0",
            "id":request_id,
            "error":{"code": -32602, "message": "unexpected error"},
        })

def statistics_handler(params, request_id, db):
    if len(params) != 1:
        return jsonify({
                "jsonrpc":"2.0",
                "id":request_id,
                "error":{
                    "code": -32602,
                    "message": "Invalid parameters: expected  one params",
                },
            }
            )

    header_hash = params.get("Hash")
    if header_hash is None or len(header_hash) != 32:
        return jsonify({
                "jsonrpc":"2.0",
                "id": request_id,
                "error":{
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            }
            )

        ## TODO: Make a rocksmain_db search function that will fetch block with needed hash. 
        # As of now returning current state

    if bytes(params["Hash"]):
        return [state.pi]
            
    else:
        return jsonify({
            "jsonrpc": "2.0",
            "id" : request_id,
            "error" : {"code": -32602, "message": "unexpected error"},
            })

def service_data_handler(params, request_id, db):
    if len(params) != 2:
        return jsonify({
                "jsonrpc":"2.0",
                "id": request_id,
                "error":{
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash and serviceId",
                },
            }
            )

    header_hash = params.get("Hash")
    service_id = params.get("ServiceId")
        
    if service_id is None:
            return jsonify({
                "jsonrpc":"2.0",
                "id":request_id,
                "error":{
                    "code": -32602,
                    "message": "Invalid parameters: expected ServiceId as single numeric item between 0 and 2^(32)−1 inclusive",
                },
                }
            )

    if header_hash is None or len(header_hash) != 32:
            return jsonify({
                "jsonrpc" : "2.0",
                "id" : request_id,
                "error" : {
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash" 
                    }
                }
            )

        #TODO: Using DeltaView to get the service data
        # DeltaView from accounts.py used in State.py

        
    if params["serviceId"]:
        return [state.delta[service_id]]              
                    
    else:
        return jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "error" : {"code": -32602, "message": "unexpected error"},
        })
    
def service_value_handler(params, request_id, db):
    if len(params) or not(params) != 3:
        return jsonify({
            "jsonrpc":"2.0",
            "id":request_id,
            "error":{
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash and ServiceId",
                },
        })

    header_hash = params.get("Hash")
    service_id = params.get("ServiceId")
    blob = params.get("Blob")
        
    if header_hash is None or len(header_hash) != 32:
        return jsonify({
            "jsonrpc" : "2.0",
            "id" : request_id,
            "error" : {
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
        })
        
    if service_id is None:
            return jsonify({
                 "jsonrpc" : "2.0",
                "id" : request_id,
                "error" : {
                    "code": -32602,
                    "message": "Invalid parameters: expected ServiceId as single numeric item between 0 and 2^(32)−1 inclusive",
                },
            } 
            )

    if blob is None:
            return jsonify({
                "jsonrpc":"2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Invalid parameters: expected Blob",
                },
                }
            )
    blob_bytes = bytes(blob)
    blob_key = ByteArray32(blob_bytes)
   
    def service_storage()-> StorageView:
        return StorageView(service_id, db, StateTrie())

    if bytes(params["Hash"]) and params["serviceId"] and params["Blob"] :
                ##TODO: resolve this correctly
        return [service_storage()[ByteArray32(blob_key)]]
            
    else:
        return jsonify({
            "jsonrpc" : "2.0",
            "id" : request_id,
            "error" : {"code": -32602, "message": "unexpected error"},
        })

def service_preimage_handler(params, request_id, db):
    if params is None or len(params) != 2:
        return jsonify({
            "jsonrpc" :"2.0",
            "id" : request_id,
            "error" : {
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash and ServiceId",
                },
        })

    header_hash = params.get("Hash")
    service_id = params.get("ServiceId")
    blob = params.get("Blob")

        
    if header_hash is None or len(header_hash) != 32:
        return jsonify({
             "jsonrpc" :"2.0",
             "id": request_id,
             "error" : {
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
        })
        
    if service_id is None:
            return jsonify({
                "jsonrpc" : "2.0",
                "id": request_id,
                "error" : {
                    "code": -32602,
                    "message": "Invalid parameters: expected ServiceId as single numeric item between 0 and 2^(32)−1 inclusive",
                },
            }
                
            )
    if blob is None:
            return jsonify({
                "jsonrpc" :"2.0",
                "id" : request_id,
                "error" : {
                    "code": -32602,
                    "message": "Invalid parameters: expected Blob",
                },
            }
                
            )
    blob_bytes = bytes(blob)
    blob_key = ByteArray32(blob_bytes)
   
    def service_preimage()-> PreImageView:
        return PreImageView(service_id, db, StateTrie())
        
        #TODO: check if service id is in the state 
    if bytes(params["Hash"]) and params["serviceId"] :
            return jsonify({
                "jsonrpc": "2.0", 
                "id" : request_id,
                "result": [service_preimage()[blob_key]]
            }
            )
    else:
            return jsonify({
                "jsonrpc" : "2.0",
                "id" : request_id,
                "error" : {"code": -32602, "message": "unexpected error"},
            }
            )
    
def service_request_handler(params, request_id, db):
    if len(params) != 4:
        return jsonify({
            "jsonrpc" : "2.0",
            "id" : request_id,
            "error": {
                "code": -32602,
                "message": "Invalid parameters: expected header_hash and ServiceId",
            },
        }
            
        )

    header_hash = params.get("Hash")
    service_id = params.get("ServiceId")
    hash = params.get("Hash")
    preimage_len = params.get("u32")

    if header_hash is None or len(header_hash) != 32:
        return jsonify({
            "jsonrpc":"2.0",
            "id":request_id,
            "error": {
                "code": -32602,
                "message": "Invalid parameters: expected header_hash",
            },
            }
        )

    if service_id is None:
        return jsonify({
            "jsonrpc":"2.0",
            "id": request_id,
            "error": {
                "code": -32602,
                "message": "Invalid parameters: expected ServiceId as single numeric item between 0 and 2^(32)−1 inclusive",
            },
        }
        )

    if hash is None:
        return jsonify({
            "jsonrpc":"2.0",
            "id": request_id,
            "error": {
                "code": -32602,
                "message": "Invalid parameters: expected hash",
            },
        }
    )

    if preimage_len is None:
        return jsonify({
            "jsonrpc" : "2.0",
            "id": request_id,
            "error": {
                "code": -32602,
                "message": "Invalid parameters: expected preimage_len",
            },
            }
        )

    def service_lookup() -> TimestampsView:
        return TimestampsView(service_id, db, StateTrie())

    # TODO: check if service id is in the state
    if params["Hash"] and params["u32"]:
        return [service_lookup()[LookupTable(hash, preimage_len)]]
    else:
        return jsonify({
            "jsonrpc":"2.0",
            "id" : request_id,
            "error" : {"code": -32602, "message": "unexpected error"},
        }
        )
