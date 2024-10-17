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

if __name__ == "__main__":
    consume_from_rabbitmq()
