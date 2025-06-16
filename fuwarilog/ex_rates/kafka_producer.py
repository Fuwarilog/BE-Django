from kafka import KafkaProducer
from numpyencoder import NumpyEncoder
import json

def send_prediction(topic, message: dict):
    def infer_schema(value: dict):
        fields = []
        for key, val in value.items():
            if isinstance(val, str):
                ftype = "string"
            elif isinstance(val, bool):
                ftype = "boolean"
            elif isinstance(val, int):
                ftype = "int64"
            elif isinstance(val, float):
                ftype = "double"
            elif isinstance(val, list):
                ftype = {"type": "array", "items": "double"}  # 기본적으로 float 리스트로 가정
            else:
                ftype = "string"  # 기본 fallback
            fields.append({"field": key, "type": ftype})
        return {
            "type": "struct",
            "fields": fields,
            "optional": False
        }

    kafka_value = {
        "schema": infer_schema(message),
        "payload": message
    }
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda m: json.dumps(m, cls=NumpyEncoder).encode('utf-8'),
    )
    producer.send(topic, kafka_value)
    producer.flush()