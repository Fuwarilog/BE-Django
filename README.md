### 📌 Django 환경
- Django 5.2
- python 3.11
- tensorflow 2.15.0
- keras 2.15.0
- numpy 1.26.4
  
</br>

### 📌 Kafka consumer 환경
- kafka-python 2.2.9
- mysqlclient 2.2.7
- PyMySQL 1.1.1

</br>

### 📌 모델 학습(가상환경과 Mysql 연동이 완료된 상태)
- models 폴더에 LSTM 모델 학습 후 저장됨
1) 모델 학습 명령어 : python scripts/train_models.py
2) 서버 구동 환경 설정 : python manage.py makemigrations
3) python manage.py migrate
4) 서버 실행 : python manage.py runserver
5) /moldes.py → train_models.py → models/* → Django ex_rates 앱 → /api/predict/ 흐름 완성


</br>
※ 주의 사항1 : tensorflow는 파이썬 3.11까지만 지원함, keras와 numpy는 tensorflow 버전에 맞춤(버전 upgrade 금지)<br>
※ 주의 사항2 : 모든 패키지는 가상환경에서 설치 할 것, 모델 학습 또한 마찬가지.
