import os
import threading
from django.apps import AppConfig

class FuwarilogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fuwarilog.ex_rates'

    def ready(self):
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
        from .kafka_consumer import start_kafka_consumer
        threading.Thread(target=start_kafka_consumer, daemon=True).start()
