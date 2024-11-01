import os
import json
import asyncio
import pika

from dotenv import load_dotenv
from notify import service

load_dotenv()

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))


# Updated async function to process message
def process_message(ch, method, properties, body):
    print(f"Processing message: {body}")
    file_data = json.loads(body)

    asyncio.run(service.execute_command(file_data.get('type'), **file_data))
    ch.basic_ack(delivery_tag=method.delivery_tag)

    print(file_data)


# def start_event_loop(loop):
#     asyncio.set_event_loop(loop)
#     loop.run_forever()


def receive_message_to_rabbitmq():
    # loop = asyncio.new_event_loop()
    # thread = Thread(target=start_event_loop, args=(loop,))
    # thread.start()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
    channel = connection.channel()
    channel.queue_declare(queue="generate_file")

    # def callback(ch, method, properties, body):
    #     asyncio.run_coroutine_threadsafe(process_message(ch, method, properties, body), loop)

    channel.basic_consume(
        queue='generate_file',
        on_message_callback=process_message,
        auto_ack=False
    )

    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    receive_message_to_rabbitmq()