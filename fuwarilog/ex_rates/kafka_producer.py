from kafka import KafkaProducer
from numpyencoder import NumpyEncoder
import json

def send_prediction(topic, data: dict):

    schema = {
        "type": "struct",
        "fields": [
            {"type": "int32", "optional": False, "field": "user_id"},
            {"type": "int32", "optional": True, "field": "trip_id"},
            {"type": "string", "optional": True, "field": "cur_nm"},
            {"type": "string", "optional": True, "field": "cur_unit"},
            {"type": "float", "optional": True, "field": "predicted_value"},
            {"type": "string", "optional": True, "field": "predict_date"}
        ],
        "optional": False,
        "name": "send01"
    }

    message = {
        "schema": schema,
        "payload": data
    }
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda m: json.dumps(m).encode('utf-8'),
    )
    producer.send(topic, message)
    producer.flush()