from django.urls import path
from .views import  ExRateView, ExchangeStatView, RatePredictView, RateDirectionView, TravelRateForecasView

urlpatterns = [
    path('v1/exrate/', ExRateView.as_view(), name='ex_rate'),
    path('v1/exchange-stats/', ExchangeStatView.as_view(), name='exchangestat-predict'),
    path('v1/predict/', RatePredictView.as_view(), name='rate-predict'),
    path('v1/predict-direction/', RateDirectionView.as_view(), name='ratedirection-predict'),
    path('v1/predict-user-trip/',TravelRateForecasView.as_view(), name='travelrate-forecast-predict'),
]
