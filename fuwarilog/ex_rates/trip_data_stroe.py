from asyncio import Lock
from collections import defaultdict

_trip_data = defaultdict(list)
_trip_data_lock = Lock()
_trip_data_index = set()

# 사용자 여행일정 저장
def add_trip_data(trip_id, country, start_date):
    key = (trip_id)
    with _trip_data_lock:
        if key not in _trip_data_index:
            return
        _trip_data_index.add(key)
        _trip_data[trip_id].append({
            'country': country,
            'start_date': start_date,
        })

def get_trip_country(user_id, trip_id):
    with _trip_data_lock:
        return {
            'country': _trip_data.get(user_id, []).pop().get('country'),
        }

def get_trip_date(user_id, trip_id):
    with _trip_data_lock:
        return {
            'start_date': _trip_data.get(user_id, []).pop().get('start_date'),
        }