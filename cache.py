import pickle
import logging
from datetime import datetime
from pathlib import Path

cache_file_name = "asset_cache.txt"
cache_data = {}  # хранилище данных кэша
cache_data['cache_file_name'] = cache_file_name
cache_logger = logging.getLogger("cache")
cache_logger.setLevel(logging.INFO)


def get_from_cache(key, max_request_age=86400):
    now = int(datetime.now().timestamp())
    if key in cache_data:
        data = cache_data[key]
        if data['timestamp'] < now - data['max_age']:
            # если данные просрочились - удалить их
            cache_logger.debug(f"{key} - cache data is too old")
            cache_data.pop(key, None)
            return None
        if data['timestamp'] >= now - max_request_age:
            # если данные по возрасту подходят то вернуть их
            cache_logger.debug(f"{key} - data got from cache")
            return data['data']
    cache_logger.debug(f"{key} - no data in cache")
    return None


def put_to_cache(key, data, max_age=300):
    now = int(datetime.now().timestamp())
    cache_data[key] = {
        "timestamp": now,
        "max_age": max_age,
        "data": data
    }
    close_cache()
    return True


def load_cache():
    global cache_data
    cache_file = Path(cache_data['cache_file_name'])
    if not cache_file.is_file():
        close_cache()
        cache_logger.info("Cache file created")
    try:
        with open(cache_data['cache_file_name'], 'rb') as cache_file:
            cache_data = {**pickle.load(cache_file), **cache_data}
    except Exception as e:
        cache_logger.error("Error loading cache file")
        cache_logger.error(e)


def close_cache():
    cache_data['cache_file_name'] = cache_file_name
    try:
        with open(cache_data['cache_file_name'], 'wb') as cache_file:
            pickle.dump(cache_data, cache_file)
    except Exception as e:
        cache_logger.error("Error writing cache")
        cache_logger.error(e)


load_cache()
