import logging
import os
import statistics
import time

from datetime import datetime
from logging.handlers import RotatingFileHandler

import requests
import schedule

from database import database, redis_database
from notification import ticker_tracking_notification

log_directory = "logs"
log_filename = "ticker_tracking.log"
log_file_path = os.path.join(log_directory, log_filename)

if not os.path.exists(log_directory):
    os.makedirs(log_directory)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = RotatingFileHandler(log_file_path, maxBytes=200000, backupCount=5)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


except_list = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "BTCDOMUSDT"]


def get_volume_data():
    main_data = requests.get('https://fapi.binance.com/fapi/v1/ticker/24hr')

    if main_data.status_code == 200:
        main_data = main_data.json()
        for ticker in main_data:
            if 'closeTime' in ticker and ticker['closeTime'] is not None:
                try:
                    ticker['openPositionDay'] = datetime.fromtimestamp(ticker['closeTime'] / 1000).strftime(
                        '%d-%m-%Y | %H')
                except (ValueError, TypeError) as e:
                    print(f"Error processing closeTime: {e}")
                    ticker['openPositionDay'] = None
            else:
                print("closeTime not found or invalid in ticker")
                ticker['openPositionDay'] = None

        current_date = statistics.mode([ticker['openPositionDay'] for ticker in main_data])
        not_usdt_symbols = [ticker['symbol'] for ticker in main_data if 'USDT' not in ticker['symbol']]
        delete_symbols = [ticker['symbol'] for ticker in main_data if ticker['openPositionDay'] != current_date]

        exchange_info_data = requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo').json()['symbols']
        not_perpetual_symbols = [info['symbol'] for info in exchange_info_data if info['contractType'] != 'PERPETUAL']
        full_symbol_list_to_delete = set(not_usdt_symbols + delete_symbols + not_perpetual_symbols)
        updated_volume_data = [ticker for ticker in main_data if ticker['symbol'] not in full_symbol_list_to_delete]

        # updated_volume_data = [d for d in volume_data if d['symbol'] not in except_list]

        return sorted(updated_volume_data, key=lambda x: float(x['priceChangePercent']), reverse=True)


def get_symbols():
    main_data = requests.get('https://fapi.binance.com/fapi/v1/ticker/24hr').json()

    for ticker in main_data:
        if 'closeTime' in ticker and ticker['closeTime'] is not None:
            try:
                ticker['openPositionDay'] = datetime.fromtimestamp(ticker['closeTime'] / 1000).strftime(
                    '%d-%m-%Y | %H')
            except (ValueError, TypeError) as e:
                print(f"Error processing closeTime: {e}")
                ticker['openPositionDay'] = None
        else:
            print("closeTime not found or invalid in ticker")
            ticker['openPositionDay'] = None

    current_date = statistics.mode([ticker['openPositionDay'] for ticker in main_data])
    not_usdt_symbols = [ticker['symbol'] for ticker in main_data if 'USDT' not in ticker['symbol']]
    delete_symbols = [ticker['symbol'] for ticker in main_data if ticker['openPositionDay'] != current_date]
    exchange_info_data = requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo').json()['symbols']
    not_perpetual_symbols = [info['symbol'] for info in exchange_info_data if info['contractType'] != 'PERPETUAL']
    full_symbol_list_to_delete = set(not_usdt_symbols + delete_symbols + not_perpetual_symbols)
    main_data = [ticker for ticker in main_data if ticker['symbol'] not in full_symbol_list_to_delete]
    ticker_list = sorted([ticker['symbol'] for ticker in main_data])
    return ticker_list


def get_funding_data():
    funding_response = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex")
    if funding_response.status_code == 200:
        funding_data = funding_response.json() if funding_response.status_code == 200 else None

        tickers = get_symbols()

        funding_rate_list = [
            {
                'symbol': value['symbol'],
                'lastFundingRate': round(float(value['lastFundingRate']) * 100, 4),
                'markPrice': float(value['markPrice']),
                'time': value['time']
            } for value in funding_data if value['symbol'] in tickers]

        sorted_data_funding = sorted(funding_rate_list, key=lambda x: float(x['lastFundingRate']))

        return sorted_data_funding


def main_runner():
    try:
        database.connect()

        tt_users = database.execute_with_return(
            """
                SELECT un.user_id, un.condition, un.id
                FROM users.user_notification un
                JOIN users.notification_settings ns ON un.user_id = ns.user_id
                WHERE un.notification_type = 'ticker_tracking' AND un.active AND ns.tracking_ticker;
            """
        )

        logger.info(f"First step, collecting all users ticker tracking {tt_users}")

        to_notify_users = []

        for tt_user in tt_users:
            notification_history = database.execute_with_return(
                """
                    SELECT date, telegram_id
                    FROM users.notification
                    WHERE type = %s
                    ORDER BY date DESC
                    LIMIT 1;
                """, (tt_user[2],))



            if notification_history:
                logger.info(f"Checking the user last notification! value: {notification_history}")

                check_last_notification = database.execute_with_return(
                    """
                        SELECT telegram_id
                        FROM users.notification
                        WHERE (%s <= NOW() - make_interval(mins := split_part(%s, '_', 1)::INTEGER)) AND telegram_id = %s;
                    """, (notification_history[0][0], tt_user[1], notification_history[0][1]))
            
            else:
                logger.info(f"User did not get any notification! value: {notification_history}")

                check_last_notification = database.execute_with_return(
                    """
                        SELECT telegram_id 
                        FROM users."user"
                        WHERE user_id = %s;
                    """, (tt_user[0],)
                )

            if check_last_notification:
                logger.info(f"{check_last_notification[0]} added to list of notification!")
                to_notify_users.append(check_last_notification[0]+tt_user)
        
        if not to_notify_users:
            database.disconnect()
            return

        tt_users = to_notify_users

        funding_data = get_funding_data()
        volume_data = get_volume_data()

        if volume_data == "Error with DB":
            logger.error("Error with DB")
            return

        notify_list = {}

        logger.info("Collected data from volume and funding data.")

        for tt_user in tt_users:
            time_interval, ticker_name = tt_user[2].split(":")
            user_telegram_id = tt_user[0]

            if ticker_name not in notify_list.keys():
                notify_list[ticker_name] = {
                    'type': tt_user[3],
                    'telegram_id': [user_telegram_id]
                }
            else:
                notify_list[ticker_name]['telegram_id'].append(user_telegram_id)

        logger.info(f"Collected telegram id of users, value of notify list: {notify_list}")


        for index, record in enumerate(volume_data):
            if record.get('symbol', None) in notify_list.keys():
                symbol_value = record.get('symbol')

                volume_data_15_min = database.execute_with_return(
                    """
                        WITH fd AS (
                            SELECT stock_id
                            FROM data_history.funding
                            WHERE symbol = %s
                        )
                        SELECT vd.last_price, vd.quote_volume
                        FROM data_history.volume_data vd
                        JOIN fd ON vd.stock_id = fd.stock_id
                        ORDER BY vd.open_time DESC
                        LIMIT 1 OFFSET 14;
                    """, (symbol_value,)
                )

                notify_list[symbol_value].update({
                    'current_price': record.get('lastPrice', 0),
                    'price_change': round((float(volume_data_15_min[0][0]) * 100 / float(record.get('lastPrice', 1))) - 100, 2),
                    'current_volume': round(float(record.get('quoteVolume', 0)), 2),
                    'volume_change': round((float(volume_data_15_min[0][1]) * 100 / float(record.get('quoteVolume', 1))) - 100, 2),
                    'top_place': index+1
                })

        for index, record in enumerate(funding_data):
            if record.get('symbol', None) in notify_list.keys():
                symbol_value = record.get('symbol')

                funding_data_15_min = database.execute_with_return(
                    """
                        WITH fd AS (
                            SELECT stock_id
                            FROM data_history.funding
                            WHERE symbol = %s
                        )
                        SELECT vd.funding_rate
                        FROM data_history.funding_data vd
                        JOIN fd ON vd.stock_id = fd.stock_id
                        ORDER BY vd.funding_time DESC
                        LIMIT 1 OFFSET 14;
                    """, (symbol_value,)
                )

                notify_list[symbol_value].update({
                    'current_funding_rate': record.get('lastFundingRate', 0),
                    'funding_rate_change': float(funding_data_15_min[0][0])
                })
        if notify_list:
            try:
                logger.info(f"Before notification function, the value of the notify list is: {notify_list}")
                ticker_tracking_notification(notify_list)
            except Exception as e:
                logger.error("Exception occurred in ticker tracking notification, error message: ", e)
    except Exception as e:
        logger.error(f"Error in main_runner: {e}")
    finally:
        database.disconnect()


schedule.every(60).seconds.do(main_runner)

while True:
    schedule.run_pending()
    time.sleep(1)

