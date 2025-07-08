
from jam.types import Hash

from tsrkit_types import structure, TypedVector

from jam.types import WorkReport, WorkReportHash


RefineVectors = TypedVector[WorkReport]
reports = [
{
  "package_spec": {
    "hash": "3af24a613bc9feea59dcd6c1e3ab44b199794e8507e2ef886eca276ea2f46f0d",
    "length": 253,
    "erasure_root": "6a0e4a8c7c232b28a3983ccc4260d0d16c81fc1550eea136dedd51c9a854a300",
    "exports_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "459cd4362e25bdcf6d6260b9cfd206b11d89a8b006d5cd32e029777385a03192",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 0,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "38f60390b2b74203d01b6c3d18700c30963aeddcbc0ce08573ae74f37f17224a",
    "length": 4425,
    "erasure_root": "27272da2c88f8106289bfbf1e0330831362e7cd0a200ecbd5cff160048ebcde3",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "587d37dafe7e73d6074d03a8eb80d14b8af552599e4437c6c68aa1f30bdaf0b6",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "bfaacb611675602f6857708283e327c3263ea951f30d07d82e3b88e36a6073e4",
    "length": 4425,
    "erasure_root": "b8880fe309668f83d395131a6b856ce2b815a562272f0de764749bd3d0d492c7",
    "exports_root": "2e2ea8b591ef3684aabc518001bf43a3ddfe6be2ada603d3501261b6b5dac2c8",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "ff22ab2fabe104fe12e79bdf463a003c8d4d6c62c786a641699cbcdbd3f2c5be",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "74a94754a42b67ae9e311fb1025f4bd7829be9711c97aef2063b47b7e19c0b04",
    "length": 8597,
    "erasure_root": "12c4aaf66b033b8064142e35c2398782fe50c6cbfc6588a4d59f2c3e51f449c7",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "e84caad83e96d576aae85146afb2e30e59429ad8122cbe6307b5aa0846f38e84",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 2,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "bd270fed16ed99478aa2665d2c70c62016a34fc6c97217cf900bfcbee3b78bfb",
    "length": 253,
    "erasure_root": "e4e1aa59f7bf14447746d8b6f5371e236a226cab4ea8c1ffeffc1c588df30ff7",
    "exports_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "ee74022d4cc61e75e595432eeed50ce258d8d7411ab31bd304d2f2d07b36ed03",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 0,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "6dfd94183345a7cc249f15dd7b709980c2db7fb85f935585634c6ac1907d345e",
    "length": 4425,
    "erasure_root": "c9484f37fd3e774965f170446340ae81dbaaecb9068728d79a60ce679194c8ad",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "b8e754e32180778355117da1d071193a144692ef83421a5840d35a8ee8946225",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "346ec33bfd7af6552e5f7c0b4b44ef8b4bd58ee509159130f5c0d318e654c4c5",
    "length": 4425,
    "erasure_root": "c244534f654772451ed687eac866f840176eaa14263e39da13a7a2c316925c81",
    "exports_root": "2e2ea8b591ef3684aabc518001bf43a3ddfe6be2ada603d3501261b6b5dac2c8",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "cc6f1d8a1bfc2119f4f5754bcbf31e08666986987e3f83bc89999d12e87c9591",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "792a7969d025c304fc6a8a71248adba37ce4e8ded9ea38d242ab027ea9884d7f",
    "length": 8597,
    "erasure_root": "76e77c120a0ff56e29cdcfc54e182decde1efad8be2d0459b7c1787a22846d9b",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "2b68b2dd11148fe0dc0fa8b924119624faf098931b634d1499224a4f151d260a",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 2,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "54202e2b8f175131ce25f8761f044625a2f833fa482cfeb64127a30513806772",
    "length": 253,
    "erasure_root": "451f6e91daf08746a38769202ddf3d2bdeb9b668612b4067ff98e4b27ce7cba5",
    "exports_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "9e81894090336a7ffdc27fd78dd3cd7a16a33e44b1a29a0bf402636d93268738",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 0,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "bac806a0eea5214540eefa6e1db49f6e316bd035c2c8bce710b03e72b63e16ec",
    "length": 4425,
    "erasure_root": "c2dd17e34c0d41dcf03787313d6f586f2760147b00fca51115f8c69ded98fab8",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "2ab9cffaa2ec3b2fb56ff2133751fdb53da77a8686a9b9feaafb16aff5f555e1",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "84ff34082a9e83440b102716746bf018dcd6dcd9600a7c243313e8abd738aa1d",
    "length": 4425,
    "erasure_root": "a5d593ffff80fd5a9b7d5c0f76635277092981a3ba8b84ce9ad52507c0cb19db",
    "exports_root": "2e2ea8b591ef3684aabc518001bf43a3ddfe6be2ada603d3501261b6b5dac2c8",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "7a6ddbd6964255dc43aa31c521e6209ed4ed66dc8503659028d8dc62a9ddf566",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "41ae4e366b429774fe3d95fb65ead4b1c32e8cb5ac989bfa6eacab2c8cce199c",
    "length": 8597,
    "erasure_root": "519855c266ef254ba66dee6ab6eb48ea951121315942fdf41faa9fc64bc66df7",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "0d9aa4422135224860cde945f6b9de2823fa7dffbc92140938c5d6e572b72174",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 2,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "2b3735d3d6c9da2b56692d5eb4ff9ef409140068163de8902908a112dfefdf78",
    "length": 253,
    "erasure_root": "adb7f64c0b1cc891d5e223691bef5a03e0e71b9cb643b3e4bccd87ed30de40b9",
    "exports_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "6102410679a89918e3779a249ce124f78c9f826d13b21c465a1910125b056b41",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 0,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "be98cfaf098f283e3d91fa548db0496f9e1d61f40244ce938335357f6f9d85b4",
    "length": 4425,
    "erasure_root": "235080b1c7d5729f745f9ed0d3710ebe606af3595ff9800b5e107b72793c4d65",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "d1776a33081bb02c856b481543f0764003543b1ea922d9b7771d0a9434c886e0",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "9dce8760a577e39da5ba7e844262cbc1cc182345ab4ff2bfa3dcfb30d795b9ef",
    "length": 4425,
    "erasure_root": "50fcfd4085b0f838392cba1daa12e475780a1606f9279c52b797826de3f8d74f",
    "exports_root": "2e2ea8b591ef3684aabc518001bf43a3ddfe6be2ada603d3501261b6b5dac2c8",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "f9ca4aa6702166ea80a8f8ed1a7b53a3cb73cc617a7f9f1c8e16d560cce521ed",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "5b958ba41c6974f0d1538c18151720eee74a1a3dad164762b5674169d11f6137",
    "length": 8597,
    "erasure_root": "bf12a5924024ef17eada36d95f45c0bb34d13a8bd637abc00ade078b5a558573",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "15b5c4f85fc9e15b4d8a314f6ec920389b77cc3bb16b5a1a87869f413ee24c4a",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 2,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "ca9bf24d7f1e9380b6f72599562a980a764dd38ae0c8f4e6d47362e655dcd24e",
    "length": 253,
    "erasure_root": "d4daaa4f43d2573037dc470039bcc5707d645bc3c7a6ada9677fba790fdc5ebf",
    "exports_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "a17c3931ae4f50b972e5510062989f27698d86e3088f21302ff5a48c1e62fe2e",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 0,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "d256bd88b9fac189712073a5c03693dc1bb0b1419150307105742f0c92e577d5",
    "length": 4425,
    "erasure_root": "23b26bd7e2a0762889396063b5a2dca2cd10766c3cfe018520e180768327cf92",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "c597fa1f7427cf1ed2b680aa7300e07507e9b1a5b9417ce1e1b3b808d6adf7f4",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "92558c345cc0e61c2925c12061efd4472e608046fbf70c8d0e470daeb28ef316",
    "length": 4425,
    "erasure_root": "777952bfb0b7235ca5ce9de95700456326b830240703852e299cbe5019986091",
    "exports_root": "2e2ea8b591ef3684aabc518001bf43a3ddfe6be2ada603d3501261b6b5dac2c8",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "651504ff4b6dcb58a011b15f8202bf4927a23df6ad126b2624cfff5f8ebc9ce0",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "ff020949787805012905a9e78d40b418ab604f8081df271edc9939d67521e8fd",
    "length": 8597,
    "erasure_root": "402892f9cfe9521369fd5d3d0a3dcbf116d3802d0d9f9e42808504ca3c343ce3",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "c6ee84e72add246f6bdfd42906f97f4163ad53c3c2b3998347f59f7bd452dd7d",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 2,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "08cc96ba8e5a1835ac404d9da2ba74c3bda3cb6df0f53c41d28370d1581cfe1b",
    "length": 253,
    "erasure_root": "fe2e6bd3f8841c863a7681383111d2e227dc55708bd1d25558c6a16239324c47",
    "exports_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "f29d03d52e7dbc32169e4910bb795a927bc177a90978e2a972e4af99b5067186",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 0,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "9e52917b540e8e7f1f4c8a6e3d370d020387f425e175ff36e9f4519f6c18bed6",
    "length": 4425,
    "erasure_root": "663e636e70aef9eede49b1a9a52849e7ae43c550c6194d6f9539f9243ecf6b43",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "4e71f9ecd1966afb913b46c451af0db9ce428bc17840eb02404ac6ccc3aff8bd",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "ebbff083ccc99e6a78ab940642c2dd6d237f2c9a99118cca22ab007cc78e6ae8",
    "length": 4425,
    "erasure_root": "80e5bc8dea5f356f7b458f70c6bf6639122819ffcd8a2dcfd4ef4b55acbd5833",
    "exports_root": "2e2ea8b591ef3684aabc518001bf43a3ddfe6be2ada603d3501261b6b5dac2c8",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "4ed95e19db019ddc8286e05b641480b204fbce8604cacc76ff0f24064065dd5f",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "8896f5d05e8f1ff78ae7c0cd96ad2940d85cb08b19999a92c6d584d2d25c93aa",
    "length": 8597,
    "erasure_root": "3f813b472a74887222c1c5f12a07cf9bd92af461a0787e3612f989a698f445b8",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "a43bea756e94892fab5900f6d9a4f9bcee54824875a753dfa120383267a184b9",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 2,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "7f01fbae913cd7a27d8c91124de1c25bbdc7f3d8471d9a8a72fe7ebfc2dae504",
    "length": 253,
    "erasure_root": "90cb56bd94123d5fb1f306d091cb11607c97e658ea02b7a9c2e3ee0e94b8c3d4",
    "exports_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "04ce79f4f6450eeb472fb858cce334dab78f38d595ac5bbc5357c19875d6d4cc",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 0,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "68bf174f58db74bf9183de4a532f77c6b8423fe3914c4ed775023053a0cb3c09",
    "length": 4425,
    "erasure_root": "f876bf6eed7920c7631d2073df1eecec3d6ad4be7623aceb00d3ca6b415e7d1a",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "1a85ae72a3af440362412acc797e264cebefc1de1756b9b189842028af8f01e3",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "5fc580de62ed4db01c09b77bb02f4f124f58baa3a19b56264fc3d51acd417930",
    "length": 4425,
    "erasure_root": "02e972e0f641c2f96b3078c32b708bef1bc0a1453a932d3ac86336b68a5b39b9",
    "exports_root": "2e2ea8b591ef3684aabc518001bf43a3ddfe6be2ada603d3501261b6b5dac2c8",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "3d3f1ea75464de7f80522faf757f96877668c91f3a0be2a18b233ada3a0c46de",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "3c8408f92e6245090a133b9dff5eba372b7fa181735d8010293c48d79569ca1a",
    "length": 8597,
    "erasure_root": "437efa6f0e7832c245ff37e5ba3c4cef2ef3bd34bac3afe909cb0e92c4acdb40",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "f271fcb8562bbc07e61a86378f9f3f752904814234bb856c8407d116e212b9fb",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 2,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "00d3a745a6bb7bca927d787bfdcb2d83a4ac8c0ad303d14013888222da3db5c0",
    "length": 253,
    "erasure_root": "31caaa340c7672eb09eee8d2e7aebdad455ab2a02b3ea2d7c837b885da8dc6fd",
    "exports_root": "3cf9b7c011a52ccd5b2513c68cde23eba207487374b074742da413d905263b91",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "b59385cd8f7c10cfcfa36ca31526854bf48a607d324bcf7398f6c93749b02871",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 0,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

{
  "package_spec": {
    "hash": "f0b7e1eab81873688d85b4c442f16082ee64327f6cb1632dea12df7e1c633a13",
    "length": 4425,
    "erasure_root": "58621f091105037e27eee268bcf3aba56c64aa0c9860b6df0526ad0984fdb05d",
    "exports_root": "6ba2490f5252ede3a7510e525b588bfaf64d8125bf3053da5586f5c11ac32694",
    "exports_count": 1
  },
  "context": {
    "anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "beefy_root": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor": "0000000000000000000000000000000000000000000000000000000000000000",
    "lookup_anchor_slot": 0,
    "prerequisites": []
  },
  "core_index": 1,
  "authorizer_hash": "d0461b410da6df4b5b28e542cd748dc356c42e93d9a0541fb61842cc8c5df1ad",
  "auth_output": "01",
  "segment_root_lookup": {},
  "results": [
    {
      "service_id": 1,
      "code_hash": "738b9aff3acbccab766e45ca4ee11d1db963cad17c9b9331b2da4b10ba40a894",
      "payload_hash": "ad83e1972dd0a604ebe9857cadf90f9a96c32cf47c7b82c804fbe83d0eaaf0af",
      "accumulate_gas": 1000,
      "result": {
        "ok": ""
      },
      "refine_load": {
        "gas_used": 49,
        "imports": 1,
        "extrinsic_count": 0,
        "extrinsic_size": 0,
        "exports": 1
      }
    }
  ],
  "auth_gas_used": 7
},

]

print(Hash.blake2b(WorkReport.from_json(reports[0]).encode()).hex())


