import json
import os

import requests
import pickle
from dotenv import load_dotenv

from database import database, redis_database


load_dotenv()

SHARED_DICT_KEY = "binance:ticker:data"
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def last_impulse_notification():
    database.connect()

    prefix = "binance:ticker:data:"

    cursor = 0
    matching_keys = []
    current_data = {}

    while True:
        cursor, keys = redis_database.scan(cursor=cursor, match=f'{prefix}*')
        matching_keys.extend(keys)

        if cursor == 0:
            break

    matching_keys = [key.decode("utf-8") for key in matching_keys]
    for key in matching_keys:
        current_data[key] = pickle.loads(redis_database.get(key))


    users = database.execute_with_return(
        """
            SELECT un.user_id, un.condition, un.id
            FROM users.user_notification un
            JOIN users.notification_settings ns ON un.user_id = ns.user_id
            WHERE un.notification_type = 'last_impulse' AND un.active AND ns.last_impulse;
        """
    )

    for user in users:
        user_interval, user_percent = user[1].split(":")
        user_percent = float(user_percent)

        for data_active, data_intervals in current_data.items():
            data_intervals = dict(data_intervals)
            temp_data = data_intervals.get(user_interval, None)

            try:
                min_diff = temp_data.get('diff', [])[0] if abs(temp_data.get('diff', [])[0]) >= user_percent else False
                max_diff = temp_data.get('diff', [])[1] if abs(temp_data.get('diff', [])[1]) >= user_percent else False
            except Exception as e:
                continue

            if temp_data and (min_diff or max_diff):
                telegram_id = database.execute_with_return(
                    """
                        SELECT telegram_id
                        FROM users."user"
                        WHERE user_id = %s;
                    """, (user[0], )
                )

                active_name = (data_active.split(":"))[-1]
                telegram_id = telegram_id[0][0]

                is_it_sent = database.execute_with_return(
                    """
                        SELECT 
                            date,
                            NOW() AS current_time,
                            (NOW() - INTERVAL '1 hour') < date AS is_less_than_one_hour
                        FROM 
                            users.notification
                        WHERE 
                            active_name = %s AND telegram_id = %s
                        ORDER BY 
                            date DESC
                        LIMIT 1;
                    """, (active_name, telegram_id)
                )

                if is_it_sent and is_it_sent[0][2]:
                    continue

                percent = min_diff if min_diff != False else max_diff

                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

                if user_interval == "1_min":
                    time_text = "(за последние 1 мин)"
                elif user_interval == "5_min":
                    time_text = "(за последние 5 мин)"
                elif user_interval == "15_min":
                    time_text = "(за последние 15 мин)"
                else:
                    time_text = "(за последние 60 мин)"

                if percent > 0:
                    text_for_notification = "\n".join(["🔔❗️Обратите внимание❗️🔔",
                                            f"Торговая пара {active_name} дала импульс цены в {percent}% {time_text} 🟢📈"])
                else:
                    text_for_notification = "\n".join(["🔔❗️Обратите внимание❗️🔔",
                                            f"Торговая пара {active_name} дала импульс цены в {percent}% {time_text} 🔴📉"])

                payload = {
                    "chat_id": telegram_id,
                    "text": text_for_notification
                }

                response = requests.post(url, json=payload)
                try:
                    day_before_price = database.execute_with_return(
                        """
                        SELECT close_price
                        FROM data_history.funding t1
                        JOIN data_history.kline_1 t2 ON t1.stock_id = t2.stock_id
                        WHERE t1.symbol = %s
                        ORDER BY t2.open_time DESC 
                        LIMIT 1 OFFSET 1439;
                        """, (active_name,)
                    )
                except Exception as e:
                    print("Error arose while making query of day_before_price: ", e)
                    continue

                current_price = temp_data.get('values', [])[-1]

                if day_before_price:
                    day_percent = round(((current_price - float(day_before_price[0][0])) / float(day_before_price[0][0])) * 100, 2)
                else:
                    day_percent = 0

                try:
                    database.execute(
                        """
                            INSERT INTO users.notification (type, date, text, status, active_name, telegram_id, percent, day_percent, params)
                            VALUES (%s, current_timestamp, %s, %s, %s, %s, %s, %s, %s);
                        """, (user[2], response.text, response.ok, active_name, telegram_id, percent, day_percent, None)
                    )
                except Exception as e:
                    print("Error arose while saving data into users.notification: ", e)

    database.disconnect()


def ticker_tracking_notification(notify_list: dict):
    print("In last impulse notification!")
    database.connect()

    for ticker_name, record in notify_list.items():
        telegram_ids = record.get("telegram_id")

        telegram_text = f"🔔Торговая пара: {ticker_name}🔔\n"

        if record.get('price_change', 0) > 0:
            telegram_text += f"– Текущая цена: {record.get('current_price')}$ ({record.get('price_change')}% за 15 мин.)🟢\n"
        else:
            telegram_text += f"– Текущая цена: {record.get('current_price')}$ ({record.get('price_change')}% за 15 мин.)🔴\n"

        if record.get('volume_change', 0) > 0:
            telegram_text += f"– Текущий объём торгов: {record.get('current_volume')}$ ({record.get('volume_change')}% за 15 мин.)🟢\n"
        else:
            telegram_text += f"– Текущий объём торгов: {record.get('current_volume')}$ ({record.get('volume_change')}% за 15 мин.)🔴\n"

        telegram_text += f"– Актив входит в ТОП {record.get('top_place')} по суточной процентности🔝\n"

        telegram_text += f" – Ставка финансирования: {record.get('current_funding_rate')}% | 15 мин. назад: {record.get('funding_rate_change')}%"

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": None,
            "text": telegram_text
        }

        for telegram_id in telegram_ids:
            payload["chat_id"] = telegram_id

            response = requests.post(url, json=payload)

            try:
                database.execute(
                    """
                        INSERT INTO users.notification (type, date, text, status, active_name, telegram_id, percent, day_percent, params)
                        VALUES (%s, current_timestamp, %s, %s, %s, %s, %s, %s, %s);
                    """, (record.get('type'), response.text, response.ok, ticker_name, telegram_id, None, None, json.dumps(record))
                )
            except Exception as e:
                print("Error arose while saving data into users.notification: ", e)