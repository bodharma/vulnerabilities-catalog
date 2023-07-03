import time, json
import pika
from harvester.config import Config
from loguru import logger


class RabbitMQ(object):
    def __init__(self, queue=None, exchange=None):
        self.queue = queue if queue else Config.getRabbitQueue()
        self.exchange = exchange if exchange else Config.getRabbitExchange()
        self.connection = Config.getRabbitConnection()
        self.channel = self.connection.channel()
        self.connect()

    def connect(self):
        logger.info(
            f"Opening RabbitMQ connection with queue {self.queue} in exchange {self.exchange} and routing key {self.queue}"
        )
        self.channel.exchange_declare(exchange=self.exchange, exchange_type="topic")
        self.channel.queue_declare(queue=self.queue)
        self.channel.queue_bind(
            exchange=self.exchange, queue=self.queue, routing_key=self.queue
        )

    def close_connection(self):
        if self.connection.is_open:
            self.connection.close()
        logger.info("RabbitMQ connection closed")

    def publish(self, messages, display_output=False):
        for message in messages:
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=self.queue,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2),
            )
            if display_output == True:
                logger.debug(f"[x] Sent! {message}")

    def callback(self, ch, method, properties, body, display_output=True):
        message = json.loads(body)
        if display_output == True:
            logger.debug(f"[x] Received {message}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        time.sleep(1)

    def flush(self):
        self.channel.queue_delete(queue=self.queue)
        self.connect()

        # consumer

    def consumer(self, callback=None):
        if callback is None:
            callback = self.callback
        logger.info("[*] Waiting for messages. To exit press CTRL+C\n\n")

        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(queue=self.queue, on_message_callback=callback)
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.error("RabbitMQ -> keyboard interruption!!!!!")
            self.channel.stop_consuming()
        finally:
            self.connection.close()


def flush(queue):
    queue.flush()
    RabbitMQ(queue.queue)


def test_producer(queue=None):
    if queue is None:
        queue = RabbitMQ("test")
    messages = [json.dumps({i: "message #" + str(i)}) for i in range(1000)]
    queue.publish(messages, display_output=True)


def test_consumer(queue=None):
    if queue is None:
        queue = RabbitMQ("test")
    queue.consumer()


def test():
    queue = RabbitMQ("test")
    test_producer(queue)
    time.sleep(5)
    test_consumer(queue)
    queue.close_connection()
