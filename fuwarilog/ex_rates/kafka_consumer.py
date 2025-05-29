import json
import os

import threading
import django
from kafka import KafkaConsumer
from .models import ExchangeRate
from datetime import datetime
from .utils import CCY_TO_COUNTRY

# Django 환경 설정
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "exchange_project.settings")
# django.setup()

def start_kafka_consumer():
    def consume():
        consumer = KafkaConsumer(
            'exchange_value_rate',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='exchange-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        print("[KafkaConsumer] Listening for prediction messages...")

        for message in consumer:
            try:
                data = message.value
                print(f"[KafkaConsumer] Received: {data}")

                cur_nm = CCY_TO_COUNTRY[data.get('cur_unit')]
                cur_unit = data.get('cur_unit')
                deal_bas_r = float(data.get('deal_bas_r', 0))
                timestamp = data.get('timestamp')

                if timestamp:
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%d").date()
                else:
                    timestamp = datetime.now().date()

                # ExchangeRate 저장
                ExchangeRate.objects.create(
                    cur_nm=cur_nm,
                    cur_unit=cur_unit,
                    deal_bas_r=deal_bas_r,
                    timestamp=timestamp
                )
                print(f"[KafkaConsumer] Saved prediction for {deal_bas_r} on {timestamp}")

            except Exception as e:
                print(f"[KafkaConsumer][ERROR] {e}")

    threading.Thread(target=consume, daemon=True).start()
