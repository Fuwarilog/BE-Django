from rest_framework import serializers
from fuwarilog.ex_rates.models import ExchangeRate

class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = '__all__'