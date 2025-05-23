from codecs import lookup
from quart import jsonify
from jam.consensus.grandpa.finality import Finality
from jam.state.merkle.merkle import StateTrie
from jam.state.state import state
from jam.types.block import Block
from jam.types.header import Header
from jam.types import  U32
from jam.types.base.sequences.bytes import ByteArray32, Bytes
from jam.state.accounts import  StorageView, PreImageView, TimestampsView
from jam.types.protocol.core import BlobLength, ServiceId
from jam.types.protocol.crypto import Hash
from jam.types.state.delta import LookupTable
from jam.state.accounts import Account

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
         
            ## using state trie function
            ## TODO: Make a rocksdb search function that will fetch block with needed hash. As of now returning current state
        if (params["Hash"]):
                # Return the parent block
                parent_block = block.load_parent(block.header.slot, db)
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
    if header_hash is None :
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
    if params["Hash"]:
        return [bytes(state.TRIE.root_hash).hex()]
    else:
        return jsonify({
            "jsonrpc":"2.0",
            "id":request_id,
            "error":{"code": -32602, "message": "unexpected error"},
        })

def statistics_handler(params, request_id, db):
    if not params :
        return jsonify({
                "jsonrpc":"2.0",
                "id":request_id,
                "error":{
                    "code": -32602,
                    "message": "Invalid parameters: expected  one params",
                },
            }
            )

    #fetch the latest updated state 
    from jam.state.state import state as updated_state

    header_hash = params.get("Hash")
    if header_hash is None:
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

    if params["Hash"]:
        return [str(updated_state.pi)]

    else:
        return jsonify({
            "jsonrpc": "2.0",
            "id" : request_id,
            "error" : {"code": -32602, "message": "unexpected error"},
            })

def service_data_handler(params, request_id, db):
    
    if not params != 2:
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

    if header_hash is None :
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
    from jam.state.state import state as updated_state

    if params["ServiceId"]:
        return [str(updated_state.delta[ServiceId(service_id)].data)]              
                    
    else:
        return jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "error" : {"code": -32602, "message": "unexpected error"},
        })
    
def service_value_handler(params, request_id, db):
    if  len(params) != 3:
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
    
    if header_hash is None :
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
    from jam.state.state import state as updated_state
    account = updated_state.delta[ServiceId(service_id)]
    storage_data = bytes(account.storage[ByteArray32(blob)])
    if  params["Blob"] :
                ##TODO: resolve this correctly
        return [str(storage_data)]
            
    else:
        return jsonify({
            "jsonrpc" : "2.0",
            "id" : request_id,
            "error" : {"code": -32602, "message": "unexpected error"},
        })

def service_preimage_handler(params, request_id, db):
    if params is None :
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

        
    if header_hash is None :
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
    from jam.state.state import state as updated_state
    account = updated_state.delta[ServiceId(service_id)]
    preimage_data = bytes(account.lookup[ByteArray32(blob)])    
        #TODO: check if service id is in the state 
    if params["ServiceId"]  and params["Blob"]:
            return [str(preimage_data)]
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
    hash = params.get("hash")
    preimage_len = params.get("u32")

    if header_hash is None:
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
    # NOTE: TimestampsView in accounts.py to be updated for this to work
    from jam.state.state import state as updated_state
    account = updated_state.delta[ServiceId(service_id)]
    hash_bytes = Bytes(hash)
    hask_key = ByteArray32(hash_bytes)
    lookup_table = LookupTable(hask_key, preimage_len)
    preimage_data = account.timestamps[lookup_table]

        #TODO: check if service id is in the state 
    if params["ServiceId"] and params["hash"] and params["u32"]:
            return [str(preimage_data)]
    else:
        return jsonify({
            "jsonrpc":"2.0",
            "id" : request_id,
            "error" : {"code": -32602, "message": "unexpected error"},
        }
        )
