import json
import threading
from kafka import KafkaConsumer
from datetime import datetime
from .models import ExchangeRate
import logging

from .utils import CCY_TO_COUNTRY

# Django 환경 설정
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "exchange_project.settings")
# django.setup()

logger = logging.getLogger(__name__)

def start_kafka_consumer():
    def consume():
        consumer = KafkaConsumer(
            'mysqlserver1.fuwarilog.exchange_rate',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='fuwarilog-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else {},
        )

        logger.info("[KafkaConsumer] Listening for prediction messages...")

        for message in consumer:
            try:
                data = message.value
                payload = data.get('payload', {})
                after = payload.get('after')

                if not after:
                    logger.warning("[KafkaConsumer] No after received!")
                    continue

                cur_nm = data.get('cur_nm')
                cur_unit = data.get('cur_unit')
                deal_bas_r = float(data.get('deal_bas_r', 0))
                timestamp = data.get('timestamp')

                if timestamp:
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%d").date()
                else:
                    timestamp = datetime.now().date()

                existing_data = ExchangeRate.objects.filter(
                    cur_unit=cur_unit, timestamp=timestamp
                ).exists()

                if existing_data:
                    logger.info(f"[KafkaConsumer] Data for {cur_unit} on {timestamp} already exists.")
                    continue

                ExchangeRate.objects.create(
                    cur_nm = cur_nm,
                    cur_unit = cur_unit,
                    deal_bas_r = deal_bas_r,
                    timestamp = timestamp
                )
                logger.info(f"[KafkaConsumer] Saved prediction for {cur_unit} on {timestamp} with rate {deal_bas_r} on {deal_bas_r}")

            except Exception as e:
                logger.error(f"[KafkaConsumer][ERROR] {e}")

    threading.Thread(target=consume, daemon=True).start()
