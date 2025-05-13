import os
import pandas as pd
from django.conf import settings
from keras.models import load_model
import joblib

# 국가→통화코드
COUNTRY_TO_CCY = {'한국':'KRW','중국':'CNY','일본':'JPY','미국':'USD'}

# 환율 값에 대한 증가/감소 예측 메서드
def get_models(ccy):
    base = settings.BASE_DIR / 'models'
    lstm = load_model(str(base / f'lstm_{ccy}.h5'), compile=False)
    tgt_scaler = joblib.load(base / f'scaler_target_{ccy}.pkl')
    return lstm, tgt_scaler

# 7일 환율 예측 메서드
def get_recent_window(ccy, window_size=30):
    df = pd.read_csv(settings.BASE_DIR / 'data' / 'data.csv', encoding='utf-8-sig', parse_dates=['적용시작일'])
    df = df[df['통화코드']==ccy].sort_values('적용시작일')
    return df.tail(window_size)

# 3개월 기간 중 최고/최저 금액 반환 메서드
def load_exchange_data(ccy):
    df = pd.read_csv('data/data.csv')
    df['적용시작일'] = pd.to_datetime(df['적용시작일'])

    # 통화코드 필터링 추가
    df = df[df['통화코드'] == ccy].copy()

    # 매매기준율 타입 보장
    df['매매기준율'] = pd.to_numeric(df['매매기준율'], errors='coerce')
    df = df.dropna(subset=['매매기준율'])

    return df