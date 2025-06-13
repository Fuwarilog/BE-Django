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
                from .kafka_consumer import start_kafka_consumer
                consumer_thread = start_kafka_consumer()

                if consumer_thread and consumer_thread.is_alive():
                    logger.info(f"[Django] Kafka consumer thread {consumer_thread.name}")
                else:
                    logger.error("[Django] Kafka consumer thread not found.")

            except Exception as e:
                logger.error(f"[Django] failed to start Kafka consumer thread {e}")

        threading.Thread(target=delayed_kafka_start, daemon=True).start()
        logger.info("[Django] Kafka Consumer initialization scheduled")