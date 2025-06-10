from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda m: json.dumps(m).encode('utf-8'),
)

def send_prediction(topic, message: dict):
    producer.send(topic, message)
    producer.flush()