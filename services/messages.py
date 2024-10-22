import pika
import os
import json


RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT')


def send_message_to_rabbitmq(message: str):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
    channel = connection.channel()

    channel.queue_declare(queue="generated_file")

    channel.basic_publish(exchange='', routing_key="generated_file", body=message)
    connection.close()