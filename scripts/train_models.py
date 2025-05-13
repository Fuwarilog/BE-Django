import os
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense

# 저장할 디렉토리
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# # 저장할 디렉토리
# MODEL_DIR = "models"
# if os.path.exists(MODEL_DIR):
#     # 실행 할 때마다 기존 모델 초기화
#     import shutil
#     shutil.rmtree(MODEL_DIR)
# os.makedirs(MODEL_DIR, exist_ok=True)


# 공통 변수
window_size = 30
currencies = ['KRW','CNY','JPY','USD']

# 전체 데이터 읽기
df = pd.read_csv('data/data.csv', encoding='utf-8-sig', parse_dates=['적용시작일'])
df = df.sort_values('적용시작일').reset_index(drop=True)

for ccy in currencies:
    # 1. 통화별 데이터
    df_ccy = df[df['통화코드']==ccy][['적용시작일','매매기준율']].copy()

    # 2. 스케일링
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df_ccy['매매기준율'].values.reshape(-1,1))

    # 3. 슬라이딩 윈도우
    X, y = [], []
    for i in range(window_size, len(scaled)):
        X.append(scaled[i-window_size:i,0])
        y.append(scaled[i,0])
    X = np.array(X).reshape(-1, window_size, 1)
    y = np.array(y)

    # 4. Train/Test 분리 (2024년 데이터 개수)
    test_len   = df_ccy[df_ccy['적용시작일'].dt.year==2024].shape[0]
    train_size = len(X) - test_len
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    # 5. LSTM 모델 학습
    lstm = Sequential([
        LSTM(64, input_shape=(window_size,1)),
        Dense(1)
    ])
    lstm.compile('adam','mse')
    lstm.fit(X_train, y_train, epochs=50, batch_size=32, verbose=1)

    # 6. 저장하기
    lstm.save(f"{MODEL_DIR}/lstm_{ccy}.h5")
    joblib.dump(scaler,     f"{MODEL_DIR}/scaler_target_{ccy}.pkl")

    print(f"{ccy} LSTM 모델 저장 완료")

print("모든 통화 LSTM 모델 학습 및 저장 완료, 위치: ./models/")
