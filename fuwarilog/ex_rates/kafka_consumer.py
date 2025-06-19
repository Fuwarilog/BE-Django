from .exchange_rate_store import add_exchange_rate
from .trip_data_stroe import add_trip_data

import json
from kafka import KafkaConsumer
from datetime import datetime
import logging
import threading
from datetime import timedelta


# Django 환경 설정
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "exchange_project.settings")
# django.setup()

# 로그 설정
logger = logging.getLogger(__name__)

# 여행 일정 환율 예측에 대한 consumer
def trip_consumer():
    def consume():
        consumer = KafkaConsumer(
            'trip.request',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='fuwarilog-trip-consumer',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else {},
            consumer_timeout_ms=30000
        )

        logger.info("[KafkaConsumer][Trip] Listening for trip data...")

        for message in consumer:
            try:
                data = message.value
                logger.info(f"[KafkaConsumer][Trip] Received message: {message.value}")

                if not isinstance(data, dict):
                    logger.warning(f"[KafkaConsumer][Trip] Received message: {data}")
                    continue

                payload = data.get('payload', {})
                op = payload.get('op')
                after = payload.get('after')

                if op == 'd' or after is None:
                    logger.info(f"[KafkaConsumer][Trip] Skipping delete or null-after message. op: {op}")
                    continue

                if not after:
                    logger.warning("[KafkaConsumer][Trip] No after received!")
                    consumer.commit()
                    continue

                trip_id = after.get('tripId')
                country = after.get('country')
                start_date = after.get('start_date')

                if not (country and start_date):
                    logger.warning("[KafkaConsumer][Trip] Skipping trip date")
                else:
                    add_trip_data(trip_id, country, start_date)
                    logger.info(f"[KafkaConsumer] Saved trip data for {trip_id}, {country}, {start_date}")

            except Exception as e:
                logger.error(f"[KafkaConsumer][Trip][ERROR] {e}")

    consumer_thread = threading.Thread(
        target=consume,
        daemon=True,
        name="trip_consumer")
    consumer_thread.start()
    logger.info('[KafkaConsumer][Trip] Consumer thread started.')

def exchange_consumer():
    def consume():
        consumer = KafkaConsumer(
            'exchange.request',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='fuwarilog-exchange-consumer',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else {},
            consumer_timeout_ms=30000
        )

        logger.info("[KafkaConsumer][Ex] Listening for prediction messages...")

        for message in consumer:
            try:
                data = message.value
                logger.info(f"[KafkaConsumer][Ex] Received message: {message.value}")

                if not isinstance(data, dict):
                    logger.warning(f"[KafkaConsumer][Ex] Received message: {data}")
                    continue

                payload = data.get('payload', {})
                op = payload.get('op')
                after = payload.get('after')

                if op == 'd' or after is None:
                    logger.info(f"[KafkaConsumer][Ex] Skipping delete or null-after message. op: {op}")
                    continue

                if not after:
                    logger.warning("[KafkaConsumer][Ex] No after received!")
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

                logger.info(f"[KafkaConsumer][Ex] Saved prediction for {cur_unit} on {timestamp} with rate {deal_bas_r} on {deal_bas_r}")

            except Exception as e:
                logger.error(f"[KafkaConsumer][ERROR] {e}")

    consumer_thread = threading.Thread(
        target=consume,
        daemon=True,
        name="exchange_consumer")
    consumer_thread.start()
    logger.info('[KafkaConsumer][Ex] Consumer thread started.')
