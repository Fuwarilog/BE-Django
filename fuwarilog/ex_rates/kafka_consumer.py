import json
from .exchange_rate_store import add_exchange_rate
from datetime import datetime, timedelta
import threading
from kafka import KafkaConsumer
from datetime import datetime
import logging

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
            consumer_timeout_ms=1000
        )

        logger.info("[KafkaConsumer] Listening for prediction messages...")

        for message in consumer:
            try:
                data = message.value
                logger.info(f"[KafkaConsumer] Received message: {message.value}")

                if not isinstance(data, dict):
                    logger.warning(f"[KafkaConsumer] Received message: {data}")
                    continue

                payload = data.get('payload', {})
                op = payload.get('op')
                after = payload.get('after')

                if op == 'd' or after is None:
                    logger.info(f"[KafkaConsumer] Skipping delete or null-after message. op: {op}")
                    continue

                if not after:
                    logger.warning("[KafkaConsumer] No after received!")
                    consumer.commit()
                    continue

                cur_nm = after.get('cur_nm')
                cur_unit = after.get('cur_unit')
                deal_bas_r = after.get('deal_bas_r')
                timestamp = after.get('timestamp')

                try:
                    deal_bas_r = float(deal_bas_r)
                except (ValueError, TypeError):
                    logger.error(f"[KafkaConsumer] deal_bas_r : {deal_bas_r}")
                    continue

                if timestamp:
                    timestamp = (datetime(1970, 1, 1) + timedelta(days=timestamp)).date()
                else:
                    timestamp = datetime.now().date()

                if cur_unit and deal_bas_r:
                    add_exchange_rate(cur_unit, timestamp, float(deal_bas_r))

                logger.info(f"[KafkaConsumer] Saved prediction for {cur_unit} on {timestamp} with rate {deal_bas_r} on {deal_bas_r}")

            except Exception as e:
                logger.error(f"[KafkaConsumer][ERROR] {e}")

    consumer_thread = threading.Thread(
        target=consume,
        daemon=True,
        name="start_kafka_consumer")
    consumer_thread.start()
    logger.info('[KafkaConsumer] Consumer thread started.')
    return consumer_thread