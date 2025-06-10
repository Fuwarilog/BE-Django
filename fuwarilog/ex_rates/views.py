from django.db.models import DateTimeField
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from fuwarilog.ex_rates.models import ExchangeRate
from .kafka_producer import send_prediction
from .serializers import ExchangeRateSerializer
from .utils import COUNTRY_TO_CCY, get_models, get_recent_window, load_exchange_data, CCY_TO_COUNTRY, get_exchange_rate
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
from datetime import datetime

# 3개월치 실시간 환율 데이터 조회
class ExRateView(APIView):
    def get(self, request):
        country = request.query_params.get('country')
        if country not in COUNTRY_TO_CCY:
            return Response({'error':'지원되지 않는 국가'}, status=status.HTTP_400_BAD_REQUEST)

        ccy = COUNTRY_TO_CCY[country]
        base_date = datetime.now()

        exchange_rate_data = ExchangeRate.objects.filter(
            cur_unit=ccy, timestamp__gte=base_date - relativedelta(months=1), timestamp__lte=base_date
        ).order_by('timestamp')

        if not exchange_rate_data:
            return Response({'error' : '해당 기간에 데이터가 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'currency': ccy,
            'country': country,
            'start_date': str(base_date - relativedelta(months=1)),
            'end_date': str(base_date),
            'list' : [
                {
                    'timestamp': str(rate.timestamp),
                    'deal_base_r': str(rate.deal_base_r)
                } for rate in exchange_rate_data
            ]
        })



class RatePredictView(APIView):
    def get(self, request):
        country = request.query_params.get('country')
        if country not in COUNTRY_TO_CCY:
            return Response({'error':'지원되지 않는 국가'}, status=status.HTTP_400_BAD_REQUEST)
        ccy = COUNTRY_TO_CCY[country]

        # 1) 모델·스케일러 로드
        lstm, tgt_scaler = get_models(ccy)

        # 2) 최근 30일 매매기준율 윈도우
        window_size = 30
        df_win = get_recent_window(ccy, window_size=window_size)
        if len(df_win) < window_size:
            return Response({'error':'충분한 데이터가 없습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3) 실제 환율 값 배열 & 정규화
        rates = df_win['deal_bas_r'].values.reshape(-1,1)
        scaled = tgt_scaler.transform(rates).flatten()

        # 4) 7일치 예측
        preds_scaled = []
        window = list(scaled)
        for _ in range(7):
            x_input = np.array(window[-window_size:]).reshape(1, window_size, 1)
            yhat = lstm.predict(x_input, verbose=0)[0,0]
            preds_scaled.append(yhat)
            window.append(yhat)

        # 5) 역스케일
        preds = tgt_scaler.inverse_transform(np.array(preds_scaled).reshape(-1,1)).flatten().tolist()

        # 6) 날짜 리스트 생성 (마지막 날짜 이후 7일)
        last_date = pd.to_datetime(df_win['timestamp'].iloc[-1])
        dates = [(last_date + pd.Timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(7)]

        # 7) 모델에 저장
        # for date, rate in zip(dates, preds):
        #     ExchangeRate.objects.create(
        #         cur_nm=country,
        #         cur_unit=ccy,
        #         timestamp=date,
        #         deal_bas_r=rate
        #     )

        send_prediction('prediction_weekly', {
            'cur_unit': ccy,
            'predicted_value': preds,
            'timestamp': (last_date + datetime.timedelta(weeks=1)).strftime('%Y-%m-%d'),
        })

        return Response({
            'currency': ccy,
            'dates': dates,
            'lstm_predictions': preds,
        })


class ExchangeStatView(APIView):
    def get(self, request):
        country = request.query_params.get('country')
        date_str = request.query_params.get('date')

        if country not in COUNTRY_TO_CCY:
            return Response({'error': '지원되지 않는 국가입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            base_date = pd.to_datetime(date_str)
        except:
            return Response({'error': '유효하지 않은 날짜 형식입니다. YYYY-MM-DD로 입력하세요.'}, status=status.HTTP_400_BAD_REQUEST)

        ccy = COUNTRY_TO_CCY[country]
        df = load_exchange_data(ccy)  # CSV 등에서 로드된 DataFrame 반환

        start_date = base_date - relativedelta(months=3)
        df_period = df[(df['적용시작일'] >= start_date) & (df['적용시작일'] <= base_date)]

        if df_period.empty:
            return Response({'error': '해당 기간에 데이터가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        max_row = df_period.loc[df_period['매매기준율'].idxmax()]
        min_row = df_period.loc[df_period['매매기준율'].idxmin()]

        return Response({
            'currency': ccy,
            'start_date': str(start_date.date()),
            'end_date': str(base_date.date()),
            'max': {
                'date': str(max_row['적용시작일']),
                'value': float(max_row['매매기준율'])
            },
            'min': {
                'date': str(min_row['적용시작일']),
                'value': float(min_row['매매기준율'])
            }
        })


class RateDirectionView(APIView):
    def get(self, request):
        country = request.query_params.get('country')
        today_rate = request.query_params.get('today_rate')

        if country not in COUNTRY_TO_CCY:
            return Response({'error': '지원되지 않는 국가입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            today_rate = float(today_rate)
        except:
            return Response({'error': '환율 값이 유효하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        ccy = COUNTRY_TO_CCY[country]
        model, scaler = get_models(ccy)
        df = get_recent_window(ccy, window_size=30)

        if len(df) < 30:
            return Response({'error': '예측에 필요한 데이터가 부족합니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        recent_rates = df['매매기준율'].values.reshape(-1, 1)
        scaled = scaler.transform(recent_rates).reshape(1, 30, 1)

        pred_scaled = model.predict(scaled, verbose=0)
        pred = scaler.inverse_transform(pred_scaled)[0][0]

        direction = (
            '상승' if pred > today_rate else
            '하락' if pred < today_rate else
            '변동 없음'
        )

        return Response({
            'currency': ccy,
            'today_rate': today_rate,
            'predicted_rate': round(pred, 2),
            'direction': direction
        })
