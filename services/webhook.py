import os

import pika
from dotenv import load_dotenv
from telegram import Bot

from i18n import i18n


TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

bot = Bot(token=TELEGRAM_BOT_TOKEN)


def process_message(ch, method, properties, body):
    print(f"Processing message: {body}")


def consume_from_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 12229))
    channel = connection.channel()

    print(channel)

    channel.queue_declare(queue='webhook_responses')

    channel.basic_consume(
        queue='webhook_responses',
        on_message_callback=process_message,
        auto_ack=True
    )

    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


# @router.get("/send_funding_data", tags=["telegram_bot"])
# async def get_funding_data_file(token_data: Dict = Depends(JWTBearer())):
#     user_id = token_data["user_id"]
#     telegram_id = token_data["telegram_id"]
#
#     csv_file_path = f"dataframes/funding_data_{user_id}.csv"
#     with open(csv_file_path, 'rb') as file:
#         await bot.send_document(chat_id=telegram_id, document=file, filename="funding_data.csv")
#
#     return {"Status": "ok"}
#
#
# @router.get("/send_volume_24hr", tags=["telegram_bot"])
# async def get_24hr_volume(file_id: int = Query(), token_data: Dict = Depends(JWTBearer())):
#     telegram_id = token_data["telegram_id"]
#
#     file_path = await database.fetchrow(
#         """
#         SELECT *
#         FROM data_history.volume_data_history
#         WHERE file_id = $1
#         """, file_id
#     )
#
#     csv_file_path = file_path.get("directory")
#     file_name = csv_file_path.split("/")[-1]
#     with open(csv_file_path, 'rb') as file:
#         await bot.send_document(chat_id=telegram_id, document=file, filename=file_name)
#
#     return {"Status": "ok"}
#
#
# @router.get("/send_growth_data", tags=["telegram_bot"])
# async def download_growth(file_id: int = Query(), token_data: Dict = Depends(JWTBearer())):
#     if not file_id:
#         return {"Provide file id!"}
#
#     user_id = token_data["user_id"]
#
#     file_params = await database.fetchrow(
#         """
#         SELECT *
#         FROM data_history.growth_data_history
#         WHERE file_id = $1 AND user_id = $2;
#         """, file_id, user_id
#     )
#
#     date_param = file_params.get("date")
#     time_param = file_params.get("time")
#     file_name = file_params.get("file_name")
#
#     csv_file_path = f"dataframes/{user_id}/{date_param}/{time_param}/{file_name}"
#     telegram_id = token_data["telegram_id"]
#
#     with open(csv_file_path, 'rb') as file:
#         await bot.send_document(chat_id=telegram_id, document=file, filename="growth_data.csv")
#
#     return {"Status": "ok"}


if __name__ == "__main__":
    consume_from_rabbitmq()
