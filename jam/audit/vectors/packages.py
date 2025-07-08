from jam.types import Hash

from tsrkit_types import structure, TypedVector

from jam.types import WorkPackage, CoreIndex, WorkReport, WorkReportHash
from jam.types.work.manifest import Extrinsics


RefineVectors = TypedVector[WorkPackage]

packages = [
{
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
{
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
{
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
{
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
{
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
{
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
{
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
{
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
{
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
{
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
},
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "65a97268aa9765236b23"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "b77696ab8c7fb285b9bb"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "4c68a8ce6564f25e2a10"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "376412a5b231686f045a"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "37e34fdcf050619310d4"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "26b6af7131a6b92d216e"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "9de09f7f550cd8b0c6d0"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "e31212b57fce6906674a"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "ccfdd7f7d941092d0f8d"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "37b0d49de25075dd9ee6"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "88740aa8519b794ed254"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "c640a4f06fca5e24eb13"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "ae64f1179564bdf0eb20"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "71575d4f063713543819"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "56ac4c9644326efd207d"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "98197613b1e17c81f412"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "fddb7dfd692ac0b902ab"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "1c5e06780abacd1d6fcb"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "d12575e1f71ec5b41c25"
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
{
  "authorization": "01",
  "auth_code_host": 42,
  "authorizer": {
    "code_hash": "1053266a8796f3fbb2936233f7b02218694b04e8604ac3c8892e415429f0a12d",
    "params": "a28f2d4a096b04d8e259"
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
]

print(WorkPackage.from_json(packages[0]))