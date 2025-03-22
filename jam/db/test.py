

from jam.rocksdb_helper import RocksDBHelper
import json
from jam.db.types import Bytes
from jam.state.state import State
from jam.types import ByteArray32

# Initialize the database (inside 'db' folder)
db = RocksDBHelper()

# Fetch the value
db_data=json.loads(db.get(b'user:1'))

# class
# genesis_transition_file = "/home/rahulcsl/jam/jam-node/tests/integration/jam-duna/state_transition/genesis_transform.json"
genesis_transition_file = "tests/integration/jam-duna/state_transition/genesis_transform.json"
key_values:dict = {}
with open(genesis_transition_file) as file:
    genesis_transition_data = json.loads(file.read())
    for i in genesis_transition_data["pre_state"]["keyvals"]:
       
        key_values[ByteArray32(Bytes(i[0]))] = bytes(Bytes(i[1]))


db_data_converted = {}

for i in db_data:
     db_data_converted[ByteArray32(i)] = bytes(Bytes(db_data[i]))

# for i in key_values:
#     print(Bytes(i).hex(),Bytes(key_values[i]).hex())

db_data_converted_sorted = {key: db_data_converted[key] for key in sorted(db_data_converted.keys())}

print("The keys and values are matching:",db_data_converted_sorted==key_values)



db_dataBhai=State.detransform(db_data_converted)
# print(db_dataBhai.delta)

# print(State.detransform(db_data_converted))


# db_state = State.detransform(db_data)
# print('xxxxx',db_state)

# for i in range(len(db_data)):
#     print(i)
# print(type(key_values))
# print(type(db_data))

    
# Close the database
db.close()

#
# # why is it showing mw error in this , wju
