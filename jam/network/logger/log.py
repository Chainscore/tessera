import os
import json
from datetime import datetime
from aioquic.quic.connection import logger

directory = "packets"

if not os.path.exists(directory):
    os.makedirs(directory)

def save_decoded_data_to_json(decoded_data, stream_id):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(directory, f"stream_{stream_id}_{timestamp}.json")

    data_dict = {
        "timestamp": timestamp,
        "stream_id": stream_id,
        "size": len(decoded_data),
        "payload_length": len(decoded_data),
        "data": decoded_data
    }

    try:
        if os.path.exists(filename):
            with open(filename, "a") as json_file:
                json_file.write(",\n")
                json.dump(data_dict, json_file, indent=4)
        else:
            with open(filename, "w") as json_file:
                json.dump(data_dict, json_file, indent=4)

        logger.info(f"📩 Data saved to {filename}")

    except Exception as e:
        logger.exception(f"Error saving decoded data to JSON file: {e}")