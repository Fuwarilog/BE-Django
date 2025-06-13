from django.db import models



# 익주 예측
class CurrencyPrediction(models.Model):
    currency_code = models.CharField(max_length=10)
    base_date = models.DateTimeField()  # 적용시작일
    predicted_rate = models.FloatField()  # 예측 환율

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.currency_code} - {self.predicted_rate}"



# 3개월 데이터 중에서 최대/최소 환율 조회
class ExchangeStats(models.Model):
    country = models.CharField(max_length=10)
    date_calculated = models.DateTimeField(auto_now_add=True)
    currency_code = models.CharField(max_length=10)
    max_rate = models.FloatField()
    min_rate = models.FloatField()
    min_rate_date = models.DateField()

    class Meta:
        db_table = "exchange_stats"

# 1주일 환율 예측
class ExchangeWeeklyPrediction(models.Model):
    country = models.CharField(max_length=10)
    prediction_date = models.DateField()   # 예측 대상 날짜
    predicted_rate = models.FloatField()
    model_version = models.CharField(max_length=20, default="v1")  # 선택사항

    class Meta:
        db_table = "exchange_weekly_pred"
        unique_together = ('country', 'prediction_date')


# 익일 상승/하락 예측
class ExchangeDirectPrediction(models.Model):
    country = models.CharField(max_length=10)
    today_rate = models.FloatField()
    predicted_tomorrow_rate = models.FloatField()
    trend = models.CharField(max_length=10)  # 'UP' or 'DOWN'
    prediction_date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "exchange_direct_pred"
        unique_together = ('country', 'prediction_date')