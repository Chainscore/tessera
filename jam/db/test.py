from jam.rocksdb_helper import RocksDBHelper
import json
from jam.db.types import Bytes
# Initialize the database (inside 'db' folder)
db = RocksDBHelper()

# Fetch the value
db_data=json.loads(db.get(b'user:1'))

# class

genesis_transition_file = "tests/integration/jam-duna/state_transition/genesis_transform.json"
key_values:dict = {}
with open(genesis_transition_file) as file:
    genesis_transition_data = json.loads(file.read())
    for i in genesis_transition_data["pre_state"]["keyvals"]:
        key_values[Bytes(i[0]).hex()] = Bytes(i[1]).hex()
        
for i in db_data:
    print(i)
# print(".........................................................................")
# for i in key_values:
#     print(i)

# for i in range(len(db_data)):
#     print(i)
# print(type(key_values))
# print(type(db_data))

    
# Close the database
db.close()

#
# # why is it showing mw error in this , wju