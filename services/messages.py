import pika
import os
import json

from dotenv import load_dotenv


load_dotenv()

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))


def process_message(ch, method, properties, body):
    print(f"Processing message: {body}")

    file_data = json.loads(body)
    print(file_data)


def receive_message_to_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
    channel = connection.channel()

    print(channel)

    channel.queue_declare(queue="generate_file")

    channel.basic_consume(
        queue='generate_file',
        on_message_callback=process_message,
        auto_ack=True
    )

    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    receive_message_to_rabbitmq()