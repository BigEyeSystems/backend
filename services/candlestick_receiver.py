from datetime import datetime
import logging
import requests
import asyncio
import aiohttp
import signal
import ssl
import os

from dotenv import load_dotenv

from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(filename='app.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

proxies_string = os.getenv('PROXIES')

proxy_list = proxies_string.split(',')


def get_symbols():
    main_data = requests.get('https://fapi.binance.com/fapi/v1/ticker/24hr').json()
    frequent_date = {}
    result_list = []

    for record in main_data:
        record['openPositionDay'] = datetime.fromtimestamp(record['closeTime'] / 1000).strftime('%d-%m-%Y')
        if record['openPositionDay'] not in frequent_date:
            frequent_date[record['openPositionDay']] = 1
        else:
            frequent_date[record['openPositionDay']] += 1

    current_date = max(frequent_date, key=frequent_date.get)

    not_usdt_symbols = [record['symbol'] for record in main_data if 'USDT' not in record['symbol']]

    delete_symbols = []
    for record in main_data:
        if record['openPositionDay'] != current_date:
            delete_symbols.append(record['symbol'])

    exchange_info_data = requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo').json()
    exchange_info_data = exchange_info_data.get('symbols')

    not_perpetual_symbols = [record['symbol'] for record in exchange_info_data if record['contractType'] != 'PERPETUAL']

    full_symbol_list_to_delete = set(not_usdt_symbols + delete_symbols + not_perpetual_symbols)

    for i in range(len(main_data)):
        if main_data[i]['symbol'] not in full_symbol_list_to_delete:
            result_list.append(main_data[i]['symbol'])

    result_list = sorted(result_list)
    return result_list


def send_message(text, attempt=1):
    alert_bot = Bot('7288064998:AAH1ggTaIexAzsDKGXI-fOQDOKY7V5Bc9Yk')
    chat_id = '588330621'
    try:
        alert_bot.sendMessage(chat_id=chat_id, text=text)
        logger.info(f'Message sent to {chat_id}: {text}')
    except TelegramError as e:
        logger.error(f'Attempt {attempt}: Failed to send message: {e.message}')
        if attempt < 5:
            attempt += 1
            send_message(chat_id, text)


def unix_to_date(unix):
    date = datetime.utcfromtimestamp((unix / 1000) + 18000).strftime('%d-%m-%Y | %H:%M')
    return date


def get_chunk_of_data(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


async def get_assets_ohlc(proxy, chunk_of_assets, directory, ssl_context=None):
    asset_streams = [f"{str(asset).lower()}@kline_1m" for asset in chunk_of_assets]
    uri = f"wss://fstream.binance.com/stream?streams={'/'.join(asset_streams)}"

    while True:
        try:
            timeout = aiohttp.ClientTimeout(sock_read=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.ws_connect(uri, proxy=proxy) as ws:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            print(f"Received data: {msg.data}")
                        elif msg.type == aiohttp.WSMsgType.PING:
                            await ws.pong(msg.data)
                            logger.info("Ping received and pong sent")
                        elif msg.type == aiohttp.WSMsgType.PONG:
                            logger.info("Pong received")
                        elif msg.type in [aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR]:
                            logger.error("WebSocket closed/error")
                            break
        except Exception as e:
            logger.error(f"An error occurred with proxy {proxy}: {e}")

        logger.error(f"Reconnecting to Binance using proxy {proxy}...")
        await asyncio.sleep(5)


# async def handle_exit(signum, frame):
#     await send_message('Script: get_asset_data\n'
#                  'Text: Script is being stopped manually.')
#     raise SystemExit
#
#
# signal.signal(signal.SIGINT, handle_exit)
# signal.signal(signal.SIGTERM, handle_exit)


async def update_symbols(queue):
    while True:
        logger.info("--> Updating symbols!")
        symbols = get_symbols()
        await queue.put(symbols)
        await asyncio.sleep(86400)


async def dispatcher(queue, proxies, directory):
    while True:
        assets = await queue.get()
        chunk_of_assets = list(get_chunk_of_data(assets, len(assets) // len(proxies)))

        tasks = [get_assets_ohlc(proxies[i], chunk_of_assets[i], directory) for i in range(len(proxies))]
        await asyncio.gather(*tasks)


async def main():
    directories = ["dataframes", "dataframes/raw_data"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    queue = asyncio.Queue()

    id_retrieving_symbols_function = asyncio.create_task(update_symbols(queue))
    dispatcher_task = asyncio.create_task(dispatcher(queue, proxy_list, directories[1]))

    await asyncio.gather(id_retrieving_symbols_function, dispatcher_task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass