import os

import requests
from dotenv import load_dotenv

from celery import shared_task
from celery_app import app
from celery.signals import worker_process_init, worker_shutdown
import pickle
from collections import deque

from database import database, redis_database as redis_client

load_dotenv()

SHARED_DICT_KEY = "binance:ticker:data"
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


# @worker_process_init.connect
# def connect_database(**kwargs):
#     try:
#         database.connect()
#         print("Database connected successfully.")
#     except Exception as e:
#         print(f"Error connecting to database: {e}")
#
#
# @worker_shutdown.connect
# def close_database_connection(**kwargs):
#     try:
#         database.disconnect()
#         print("Database connection closed successfully.")
#     except Exception as e:
#         print(f"Error closing database connection: {e}")


@app.task
def push_stock_data(stock_symbol, new_data: float):
    stock_key = f"{SHARED_DICT_KEY}:{stock_symbol}"

    if not redis_client.exists(stock_key):
        shared_dict = {
            "1_min": {
                "value": None,
                "diff": []
            },
            "5_min": {
                "values" : deque(maxlen=5),
                "min": None,
                "max": None,
                "diff": []
            },
            "15_min": {
                "values": deque(maxlen=15),
                "min": None,
                "max": None,
                "diff": []
            },
            "60_min": {
                "values": deque(maxlen=60),
                "min": None,
                "max": None,
                "diff": []
            },
        }
    else:
        shared_dict = pickle.loads(redis_client.get(stock_key))

    for interval_type, current_data in shared_dict.items():
        if interval_type == "1_min":
            if current_data.get("value"):
                old_data = current_data.get("value", 0.001)
                current_data["diff"] = [old_data - new_data,
                                        round((old_data - new_data) / abs(old_data) * 100, 3)]
            else:
                current_data["diff"] = [new_data, 0]

            current_data["value"] = float(new_data)
        else:
            sliding_window = current_data.get("values")
            sliding_window.append(new_data)

            min_value = min(sliding_window[:-1])
            max_value = max(sliding_window[:-1])

            current_data["diff"] = [round((min_value - new_data) / abs(new_data) * 100, 3),
                                    round((max_value - new_data) / abs(new_data) * 100, 3)
                                    ]
            current_data["min"] = min_value
            current_data["max"] = max_value

    redis_client.set(stock_key, pickle.dumps(shared_dict))
    redis_client.expire(stock_key, 3600)

    cursor = 0
    while True:
        cursor, keys = redis_client.scan(cursor=cursor, match='celery-task-meta*', count=10000)
        if keys:
            redis_client.delete(*keys)
        if cursor == 0:
            break


@app.task
def update_stock_data(stock_symbol, new_data: float):
    stock_key = f"{SHARED_DICT_KEY}:{stock_symbol}"
    try:
        shared_dict = pickle.loads(redis_client.get(stock_key))
    except:
        return "create_stock_key"

    for interval_type, current_data in shared_dict.items():
        if interval_type == "1_min":
            if current_data.get("value"):
                old_data = current_data.get("value", 0.001)
                current_data["diff"] = [old_data - new_data,
                                        round((old_data - new_data) / abs(old_data) * 100, 3)]
            else:
                current_data["diff"] = [new_data, 0]
        else:
            sliding_window = current_data.get("values")
            sliding_window[-1] = new_data

            current_data["diff"] = [round((current_data["min"] - new_data) / abs(new_data) * 100, 3),
                                    round((current_data["max"] - new_data) / abs(new_data) * 100, 3)
                                    ]

    redis_client.set(stock_key, pickle.dumps(shared_dict))
    redis_client.expire(stock_key, 3600)
    return "success"
