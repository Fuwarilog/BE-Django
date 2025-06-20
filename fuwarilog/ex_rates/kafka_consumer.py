from django.db.models.signals import post_save

from .exchange_rate_store import add_exchange_rate
from .trip_data_stroe import add_trip_data

import json
from kafka import KafkaConsumer
from datetime import datetime
import logging
import threading
from datetime import timedelta
import requests
from datetime import date


# Django 환경 설정
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "exchange_project.settings")
# django.setup()

# 로그 설정
logger = logging.getLogger(__name__)

# 여행 일정 환율 예측에 대한 consumer

def trip_consumer():
    def consume():
        consumer = KafkaConsumer(
            'triprequest',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='fuwarilog-trip-consumer-3',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else {},
            consumer_timeout_ms=3000
        )

        logger.info("[KafkaConsumer][Trip] Listening for trip data...")

        for message in consumer:
            try:
                data = message.value
                logger.info(f"[KafkaConsumer][Trip] Received message: {message.value}")

                user_id = data.get('userId')
                trip_id = data.get('tripId')
                country = data.get('country')
                start_date_list = data.get('startDate')

                # [yyyy, MM, dd] list 형식 -> yyyy-MM-dd 형식 srt 변환
                start_date = normalize_date(start_date_list)

                if not (user_id or trip_id or country or start_date):
                    logger.warning("[KafkaConsumer][Trip] Skipping trip date")
                else:
                    add_trip_data(user_id, trip_id, country, start_date)
                    logger.info(f"[KafkaConsumer] Saved trip data for {user_id}, {trip_id}, {country}, {start_date}")

                requests.get(f"http://127.0.0.1:8000/api/v1/predict-user-trip/?user_id={user_id}&trip_id={trip_id}")

            except Exception as e:
                logger.error(f"[KafkaConsumer][Trip][ERROR] {e}")

    consumer_thread = threading.Thread(
        target=consume,
        daemon=True,
        name="trip_consumer")
    consumer_thread.start()
    logger.info('[KafkaConsumer][Trip] Consumer thread started.')

    def normalize_date(date_input):
        if isinstance(date_input, list) and len(date_input) == 3:
            try:
                return date(date_input[0], date_input[1], date_input[2]).strftime("%Y-%m-%d")
            except Exception as e:
                logger.error(f"[KafkaConsumer][Trip] Invalid date array: {date_input}, Error: {e}")
                return None
        elif isinstance(date_input, str):
            return date_input
        else:
            logger.warning(f"[KafkaConsumer][Trip] Unsupported date format: {date_input}")
            return None

# def exchange_consumer():
#     def consume():
#         consumer = KafkaConsumer(
#             'exchange.request',
#             bootstrap_servers='localhost:9092',
#             auto_offset_reset='latest',
#             enable_auto_commit=True,
#             group_id='fuwarilog-exchange-consumer',
#             value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else {},
#             consumer_timeout_ms=30000
#         )
#
#         logger.info("[KafkaConsumer][Ex] Listening for prediction messages...")
#
#         for message in consumer:
#             try:
#                 data = message.value
#                 logger.info(f"[KafkaConsumer][Ex] Received message: {message.value}")
#
#                 if not isinstance(data, dict):
#                     logger.warning(f"[KafkaConsumer][Ex] Received message: {data}")
#                     continue
#
#                 payload = data.get('payload', {})
#                 op = payload.get('op')
#                 after = payload.get('after')
#
#                 if op == 'd' or after is None:
#                     logger.info(f"[KafkaConsumer][Ex] Skipping delete or null-after message. op: {op}")
#                     continue
#
#                 if not after:
#                     logger.warning("[KafkaConsumer][Ex] No after received!")
#                     consumer.commit()
#                     continue
#
#                 cur_nm = after.get('cur_nm')
#                 cur_unit = after.get('cur_unit')
#                 deal_bas_r = after.get('deal_bas_r')
#                 timestamp = after.get('timestamp')
#
#                 try:
#                     deal_bas_r = float(deal_bas_r)
#                 except (ValueError, TypeError):
#                     logger.error(f"[KafkaConsumer] deal_bas_r : {deal_bas_r}")
#                     continue
#
#                 if timestamp:
#                     timestamp = (datetime(1970, 1, 1) + timedelta(days=timestamp)).date()
#                 else:
#                     timestamp = datetime.now().date()
#
#                 if cur_unit and deal_bas_r:
#                     add_exchange_rate(cur_unit, timestamp, float(deal_bas_r))
#
#                 logger.info(f"[KafkaConsumer][Ex] Saved prediction for {cur_unit} on {timestamp} with rate {deal_bas_r} on {deal_bas_r}")
#
#             except Exception as e:
#                 logger.error(f"[KafkaConsumer][ERROR] {e}")
#
#     consumer_thread = threading.Thread(
#         target=consume,
#         daemon=True,
#         name="exchange_consumer")
#     consumer_thread.start()
#     logger.info('[KafkaConsumer][Ex] Consumer thread started.')
