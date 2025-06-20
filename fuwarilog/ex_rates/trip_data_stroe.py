from threading import Lock
from collections import defaultdict

_trip_data = defaultdict(list)
_trip_data_lock = Lock()
_trip_data_index = set()

# 사용자 여행일정 저장
def add_trip_data(user_id, trip_id, country, start_date):
    key = (user_id, trip_id)
    with _trip_data_lock:
        if key in _trip_data_index:
            return
        _trip_data_index.add(key)
        _trip_data[user_id].append({
            'trip_id': trip_id,
            'country': country,
            'start_date': start_date,
        })

def get_trip_country(user_id, trip_id):
    with _trip_data_lock:
        for trip in _trip_data.get(user_id, []):
            if trip['trip_id'] == trip_id:
                return trip.get('country')
        return None

def get_trip_date(user_id, trip_id):
    with _trip_data_lock:
        for trip in _trip_data.get(user_id, []):
            if trip['trip_id'] == trip_id:
                return trip.get('start_date')
        return None