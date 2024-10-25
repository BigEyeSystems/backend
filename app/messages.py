import pika
import os


RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')


def send_message_to_rabbitmq(message: str):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    # Ensure the queue exists
    channel.queue_declare(queue=QUEUE_NAME)

    # Send the message
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=message)
    connection.close()