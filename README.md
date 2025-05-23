### 📌 Django 환경
- Django==5.2
- python 3.11
- tensorflow 2.15.0
- keras 2.15.0
- numpy 1.26.4
  
</br>

### 📌 Kafka consumer 환경
- kafka-python
- pymysql

</br>

### 📌 모델 학습
- models 폴더에 LSTM 모델 학습 후 저장됨
- 모델 학습 명령어 : python scripts/train_models.py


</br>
※ 주의 사항1 : tensorflow는 파이썬 3.11까지만 지원함, keras와 numpy는 tensorflow 버전에 맞춤(버전 upgrade 금지) \n

※ 주의 사항2 : 모든 패키지는 가상환경에서 설치 할 것, 모델 학습 또한 마찬가지.
</br>
