from collections import defaultdict
from threading import Lock

_exchange_rate_data = defaultdict(list)  # key: cur_unit, value: list of dicts
_exchange_rate_lock = Lock()
_exchange_rate_index = set()

def add_exchange_rate(cur_unit, timestamp, deal_bas_r):
    key = (cur_unit, timestamp)
    with _exchange_rate_lock:
        if key in _exchange_rate_index:
            return
        _exchange_rate_index.add(key)
        _exchange_rate_data[cur_unit].append({
            'timestamp': timestamp,
            'deal_bas_r': deal_bas_r
        })

def get_exchange_rates(cur_unit, start_date, end_date):
    with _exchange_rate_lock:
        return [
            rate for rate in _exchange_rate_data.get(cur_unit, [])
            if start_date <= rate['timestamp'] <= end_date
        ]

def get_exchange_rates_max_min(cur_unit):
    with _exchange_rate_lock:
        return [
            _exchange_rate_data.get(cur_unit, [])
        ]

# def get_exchange_rate_date(cur_unit, base_date):
#     with _exchange_rate_lock:
#         return {
#             rate for rate in _exchange_rate_data.get(cur_unit, [])
#             if rate['timestamp'] == base_date
#         }