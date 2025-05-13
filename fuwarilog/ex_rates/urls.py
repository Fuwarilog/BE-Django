from django.urls import path
from .views import RatePredictView, ExchangeStatView, RateDirectionView

urlpatterns = [
    path('predict/', RatePredictView.as_view(), name='rate-predict'),
    path('exchange-stats/', ExchangeStatView.as_view(), name='exchangestat-predict'),
    path('predict-direction/', RateDirectionView.as_view(), name='ratedirection-predict'),
]
