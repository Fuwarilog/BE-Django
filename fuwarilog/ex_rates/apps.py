import os
import threading
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class FuwarilogConfig(AppConfig):

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fuwarilog.ex_rates'

    def ready(self):
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
        def delayed_kafka_start():
            try:
                from .kafka_consumer import trip_consumer #, exchange_consumer
                consumer_thread1 = trip_consumer()
                # consumer_thread2 = exchange_consumer()

                if consumer_thread1 and consumer_thread1.is_alive():
                    logger.info(f"[Django] Trip consumer thread {consumer_thread1.name}")
                else:
                    logger.error("[Django] Trip consumer thread not found.")

                # if consumer_thread2 and consumer_thread2.is_alive():
                #     logger.info(f"[Django] Exchange consumer thread {consumer_thread2.name}")
                # else:
                #     logger.error("[Django] Exchange consumer thread not found.")

            except Exception as e:
                logger.error(f"[Django] failed to start Kafka consumer thread {e}")

        threading.Thread(target=delayed_kafka_start, daemon=True).start()
        logger.info("[Django] Kafka Consumer initialization scheduled")