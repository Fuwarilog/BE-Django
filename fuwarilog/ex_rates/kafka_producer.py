from kafka import KafkaProducer
from numpyencoder import NumpyEncoder
import json

def send_prediction(topic, message: dict):

    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda m: json.dumps(m, cls=NumpyEncoder).encode('utf-8'),
    )
    producer.send(topic, message)
    producer.flush()