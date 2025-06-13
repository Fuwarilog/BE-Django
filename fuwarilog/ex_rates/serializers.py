from rest_framework import serializers

class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'