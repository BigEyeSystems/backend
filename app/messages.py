import pika
import os
import json


RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))


def send_message_to_rabbitmq(message: dict, queue: str):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
    channel = connection.channel()

    channel.queue_declare(queue=queue)

    json_message = json.dumps(message)

    channel.basic_publish(
        exchange='',
        routing_key=queue,
        body=json_message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        )
    )
    connection.close()