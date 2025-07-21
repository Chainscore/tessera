from jam.types import Hash

from tsrkit_types import structure, TypedVector

from jam.types import WorkPackage
from jam.types.work.manifest import Extrinsics


RefineVectors = TypedVector[WorkPackage]




hash_to_package = [
    {
  "3af24a613bc9feea59dcd6c1e3ab44b199794e8507e2ef886eca276ea2f46f0d": {
    "authorization": "01",
    "auth_code_host": 42,
    "authorizer": {
      "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
      "params": "d914a1f4c711d703a16f"
    },
    "context": {
      "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor_slot": 0,
      "prerequisites": []
    },
    "items": [
      {
        "service": 1,
        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
        "payload": "626f6261626f6261",
        "refine_gas_limit": 1000,
        "accumulate_gas_limit": 1000,
        "import_segments": [],
        "extrinsic": [],
        "export_count": 1
      }
    ]
  },
  "38f60390b2b74203d01b6c3d18700c30963aeddcbc0ce08573ae74f37f17224a": {
    "authorization": "01",
    "auth_code_host": 42,
    "authorizer": {
      "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
      "params": "34401c7359774f241912"
    },
    "context": {
      "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor_slot": 0,
      "prerequisites": []
    },
    "items": [
      {
        "service": 1,
        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
        "payload": "626f6261626f6261",
        "refine_gas_limit": 1000,
        "accumulate_gas_limit": 1000,
        "import_segments": [
          {
            "tree_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
            "index": 0
          }
        ],
        "extrinsic": [],
        "export_count": 1
      }
    ]
  },
  "bfaacb611675602f6857708283e327c3263ea951f30d07d82e3b88e36a6073e4": {
    "authorization": "01",
    "auth_code_host": 42,
    "authorizer": {
      "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
      "params": "bcf3588ab585a854fe37"
    },
    "context": {
      "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor_slot": 0,
      "prerequisites": []
    },
    "items": [
      {
        "service": 1,
        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
        "payload": "626f6261626f6261",
        "refine_gas_limit": 1000,
        "accumulate_gas_limit": 1000,
        "import_segments": [
          {
            "tree_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
            "index": 0
          }
        ],
        "extrinsic": [],
        "export_count": 1
      }
    ]
  },
  "74a94754a42b67ae9e311fb1025f4bd7829be9711c97aef2063b47b7e19c0b04": {
    "authorization": "01",
    "auth_code_host": 42,
    "authorizer": {
      "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
      "params": "7c527627ba6fac003b71"
    },
    "context": {
      "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor_slot": 0,
      "prerequisites": []
    },
    "items": [
      {
        "service": 1,
        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
        "payload": "626f6261626f6261",
        "refine_gas_limit": 1000,
        "accumulate_gas_limit": 1000,
        "import_segments": [
          {
            "tree_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
            "index": 0
          },
          {
            "tree_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
            "index": 0
          }
        ],
        "extrinsic": [],
        "export_count": 1
      }
    ]
  },
  "bd270fed16ed99478aa2665d2c70c62016a34fc6c97217cf900bfcbee3b78bfb": {
    "authorization": "01",
    "auth_code_host": 42,
    "authorizer": {
      "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
      "params": "385e673167ab28c7aac5"
    },
    "context": {
      "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor_slot": 0,
      "prerequisites": []
    },
    "items": [
      {
        "service": 1,
        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
        "payload": "626f6261626f6261",
        "refine_gas_limit": 1000,
        "accumulate_gas_limit": 1000,
        "import_segments": [],
        "extrinsic": [],
        "export_count": 1
      }
    ]
  },
  "6dfd94183345a7cc249f15dd7b709980c2db7fb85f935585634c6ac1907d345e": {
    "authorization": "01",
    "auth_code_host": 42,
    "authorizer": {
      "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
      "params": "6390331f1cfbb37ea5f0"
    },
    "context": {
      "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor_slot": 0,
      "prerequisites": []
    },
    "items": [
      {
        "service": 1,
        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
        "payload": "626f6261626f6261",
        "refine_gas_limit": 1000,
        "accumulate_gas_limit": 1000,
        "import_segments": [
          {
            "tree_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
            "index": 0
          }
        ],
        "extrinsic": [],
        "export_count": 1
      }
    ]
  },
  "346ec33bfd7af6552e5f7c0b4b44ef8b4bd58ee509159130f5c0d318e654c4c5": {
    "authorization": "01",
    "auth_code_host": 42,
    "authorizer": {
      "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
      "params": "4af728b0df0786f2272a"
    },
    "context": {
      "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor_slot": 0,
      "prerequisites": []
    },
    "items": [
      {
        "service": 1,
        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
        "payload": "626f6261626f6261",
        "refine_gas_limit": 1000,
        "accumulate_gas_limit": 1000,
        "import_segments": [
          {
            "tree_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
            "index": 0
          }
        ],
        "extrinsic": [],
        "export_count": 1
      }
    ]
  },
  "792a7969d025c304fc6a8a71248adba37ce4e8ded9ea38d242ab027ea9884d7f": {
    "authorization": "01",
    "auth_code_host": 42,
    "authorizer": {
      "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
      "params": "d0861896b74f3b972ade"
    },
    "context": {
      "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor_slot": 0,
      "prerequisites": []
    },
    "items": [
      {
        "service": 1,
        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
        "payload": "626f6261626f6261",
        "refine_gas_limit": 1000,
        "accumulate_gas_limit": 1000,
        "import_segments": [
          {
            "tree_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
            "index": 0
          },
          {
            "tree_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
            "index": 0
          }
        ],
        "extrinsic": [],
        "export_count": 1
      }
    ]
  },
  "54202e2b8f175131ce25f8761f044625a2f833fa482cfeb64127a30513806772": {
    "authorization": "01",
    "auth_code_host": 42,
    "authorizer": {
      "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
      "params": "30d3b416e759549dd95c"
    },
    "context": {
      "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor_slot": 0,
      "prerequisites": []
    },
    "items": [
      {
        "service": 1,
        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
        "payload": "626f6261626f6261",
        "refine_gas_limit": 1000,
        "accumulate_gas_limit": 1000,
        "import_segments": [],
        "extrinsic": [],
        "export_count": 1
      }
    ]
  },
  "bac806a0eea5214540eefa6e1db49f6e316bd035c2c8bce710b03e72b63e16ec": {
    "authorization": "01",
    "auth_code_host": 42,
    "authorizer": {
      "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
      "params": "c236f208a0ec8a0c3ed0"
    },
    "context": {
      "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
      "lookup_anchor_slot": 0,
      "prerequisites": []
    },
    "items": [
      {
        "service": 1,
        "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
        "payload": "626f6261626f6261",
        "refine_gas_limit": 1000,
        "accumulate_gas_limit": 1000,
        "import_segments": [
          {
            "tree_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
            "index": 0
          }
        ],
        "extrinsic": [],
        "export_count": 1
      }
    ]
  }
}
]

hash_value = "bac806a0eea5214540eefa6e1db49f6e316bd035c2c8bce710b03e72b63e16ec"

found = None

for package in hash_to_package:
    for key, value in package.items():
        if key == hash_value:
            found = value
            break  # optional: stops early if found
    if found:
        break

if found:
    import json
    print(json.dumps(found, indent=2))
else:
    print("Hash not found.")






# Create the mapping
# hash_to_package = {hash_value: package for hash_value, package in zip(hash_values, packages)}
#
# # Optional: Print the result as JSON
# import json
#
# print(json.dumps(hash_to_package, indent=2))