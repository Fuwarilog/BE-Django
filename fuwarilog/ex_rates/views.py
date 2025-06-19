from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from fuwarilog.authentication import JWTAuthentication
from .serializers import ExchangeRateSerializer
from .kafka_producer import send_prediction
from .trip_data_stroe import get_trip_country, get_trip_date
from .utils import COUNTRY_TO_CCY, get_models, get_exchange_data
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
from datetime import timedelta
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 3개월/1개월치 실시간 환율 데이터 조회
class ExRateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        #user = request.user
        country = request.query_params.get('country')
        date = request.query_params.get('date') # 1w: week, 1m: month, 3m: 3month

        if country not in COUNTRY_TO_CCY:
            return Response({'error':'지원되지 않는 국가'}, status=status.HTTP_400_BAD_REQUEST)

        ccy = COUNTRY_TO_CCY[country]
        end_date = datetime.now().date()

        if date == "1w":
            start_date = end_date - relativedelta(days=7)
        elif date == "1m":
            start_date = end_date - relativedelta(months=1)
        elif date == "3m":
            start_date = end_date - relativedelta(months=3)

        exchange_data = get_exchange_data(ccy, start_date, end_date)
        serializer = ExchangeRateSerializer(exchange_data, many=True)

        if not exchange_data:
            return Response({'error' : '해당 기간에 데이터가 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)


# 1개월 동안의 최고/최저 환율 조회
class ExchangeStatView(APIView):
    def get(self, request):
        country = request.query_params.get('country')
        date_str = request.query_params.get('date')

        if country not in COUNTRY_TO_CCY:
            return Response({'error': '지원되지 않는 국가입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            end_date = pd.to_datetime(date_str).date()
        except:
            return Response({'error': '유효하지 않은 날짜 형식입니다. YYYY-MM-DD로 입력하세요.'}, status=status.HTTP_400_BAD_REQUEST)

        ccy = COUNTRY_TO_CCY[country]
        start_date = end_date - relativedelta(months=3)

        exchange_data = get_exchange_data(ccy, start_date, end_date)
        serializer = ExchangeRateSerializer(exchange_data, many=True)

        if not exchange_data:
            return Response({'error': '해당 기간에 데이터가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        df = pd.DataFrame(serializer.data)
        max_row = df.loc[df['deal_bas_r'].idxmax()]
        min_row = df.loc[df['deal_bas_r'].idxmin()]

        return Response({
            'currency': ccy,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'max': {
                'date': str(max_row['timestamp']),
                'value': float(max_row['deal_bas_r'])
            },
            'min': {
                'date': str(min_row['timestamp']),
                'value': float(min_row['deal_bas_r'])
            }
        })

# 익주 예측(기본-mysql 조회)
class RatePredictView(APIView):
    def get(self, request):
        country = request.query_params.get('country')
        if country not in COUNTRY_TO_CCY:
            return Response({'error':'지원되지 않는 국가'}, status=status.HTTP_400_BAD_REQUEST)
        ccy = COUNTRY_TO_CCY[country]

        # 1) 모델·스케일러 로드
        lstm, tgt_scaler = get_models(ccy)

        # 2) 최근 30일 매매기준율 윈도우
        all_data = get_exchange_data(ccy, datetime.min.date(), datetime.now().date())
        if len(all_data) < 30:
            return Response({'error': '충분한 데이터가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        df = pd.DataFrame(all_data)
        df = df.sort_values(by='timestamp')
        df_win = df.tail(30)

        # 3) 실제 환율 값 배열 & 정규화
        rates = df_win['deal_bas_r'].values.reshape(-1, 1)
        scaled = tgt_scaler.transform(rates).flatten()

        # 4) 7일치 예측
        preds_scaled = []
        window = list(scaled)
        for _ in range(7):
            x_input = np.array(window[-30:]).reshape(1, 30, 1)
            yhat = lstm.predict(x_input, verbose=0)[0, 0]
            preds_scaled.append(yhat)
            window.append(yhat)

        # 5) 역스케일
        preds = tgt_scaler.inverse_transform(np.array(preds_scaled).reshape(-1, 1)).flatten().tolist()

        # 6) 날짜 리스트 생성 (마지막 날짜 이후 7일)
        last_date = pd.to_datetime(df_win['timestamp'].iloc[-1])
        dates = [(last_date + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(7)]

        for i in range(7):
            send_prediction('prediction_weekly', {
                'cur_unit': ccy,
                'predicted_value': preds[i],
                'timestamp': dates[i],
            })

        return Response({
            'currency': ccy,
            'dates': dates,
            'lstm_predictions': preds,
        })


# 익일 예측(기본-mysql에서 조회)
class RateDirectionView(APIView):
    def get(self, request):
        country = request.query_params.get('country')
        today = request.query_params.get('today')

        if country not in COUNTRY_TO_CCY:
            return Response({'error': '지원되지 않는 국가입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            base_date = pd.to_datetime(today).date()
        except:
            return Response({'error': '유효하지 않은 날짜 형식입니다. YYYY-MM-DD로 입력하세요.'}, status=status.HTTP_400_BAD_REQUEST)

        ccy = COUNTRY_TO_CCY[country]
        logger.info(ccy)
        model, scaler = get_models(ccy)

        all_data = get_exchange_data(ccy, datetime.min.date(), datetime.now().date())
        if len(all_data) < 30:
            return Response({'error': '예측에 필요한 데이터가 부족합니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        df = pd.DataFrame(all_data).sort_values(by='timestamp').tail(30)
        rates = df['deal_bas_r'].values.reshape(-1, 1)
        scaled = scaler.transform(rates).reshape(1, 30, 1)

        today_rate = df[(df['timestamp'] == base_date)]
        today_rate_val = float(today_rate.iloc[0]['deal_bas_r'])

        pred_scaled = model.predict(scaled, verbose=0)
        pred = float(scaler.inverse_transform(pred_scaled)[0][0])

        direction = (
            '상승' if pred > today_rate_val else
            '하락' if pred < today_rate_val else
            '변동 없음'
        )

        send_prediction('prediction_daily', {
            'cur_nm': country,
            'cur_unit': ccy,
            'predicted_rate': pred,
            'today_rate': today_rate_val,
            'direction': direction,
            'predicted_date': (base_date + timedelta(days=1)).strftime('%Y-%m-%d')
        })

        return Response({
            'currency': ccy,
            'predicted_date': today_rate_val,
            'predicted_rate': round(pred, 3),
            'direction': direction
        })

# 사용자 여행 일정의 일주일 전 환율 예측 기능
class TravelRateForecasView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_id = user.user_id # 쿠키의 accessToken을 통해 mysql에 저장되어있는 userId와 동일한지 확인하고 user_id 추출
        trip_id = request.query_params.get('tripId') # localhost:3000에서 전달한 값

        country = get_trip_country(user_id, trip_id)
        start_date = get_trip_date(user_id, trip_id)

        if not (country and start_date):
            return Response({'error': 'country, startDate는 필수로 입력해야합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        if country not in COUNTRY_TO_CCY:
            return Response({'error': '지원되지 않는 국가입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = pd.to_datetime(start_date).date()
        except:
            return Response({'error': '날짜 형식이 유효하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        ccy = COUNTRY_TO_CCY[country]
        model, scaler = get_models(ccy)

        all_data = get_exchange_data(ccy, datetime.min.date(), datetime.now().date())
        if len(all_data) < 30:
            return Response({'error': '예측에 필요한 데이터가 부족합니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        df = pd.DataFrame(all_data)
        df = df.sort_values(by='timestamp')
        df_win = df.tail(30)

        rates = df_win['deal_bas_r'].values.reshape(-1, 1)
        scaled = scaler.transform(rates).flatten().tolist()

        num_days = 7
        preds_scaled = []
        window = list(scaled)

        for _ in range(num_days):
            x_input = np.array(window[-30:]).reshape(-1, 30, 1)
            yhat = model.predict(x_input, verbose=0)[0][0]
            preds_scaled.append(yhat)
            window.append(yhat)

        preds = scaler.inverse_transform(np.array(preds_scaled).reshape(-1, 1))

        predict_dates = [(start_date - timedelta(days=(7-1))).strftime('%Y-%m-%d')]

        for i in range(7):
            send_prediction('prediction_trip_weekly', {
                'user_id': user_id,
                'trip_id': trip_id,
                'cur_nm': country,
                'cur_unit': ccy,
                'predicted_value': preds[i],
                'predict_dates': predict_dates[i],
            })

        return Response({
            'user_id': user_id,
            'trip_id': trip_id,
            'cur_nm': country,
            'cur_unit': ccy,
            'predicted_values': [round(p, 3) for p in preds],
            'predict_dates': predict_dates,
        })
