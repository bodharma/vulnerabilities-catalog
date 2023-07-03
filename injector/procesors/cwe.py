from injector.rabbit.rabbit_consumer import RabbitMQConsumer
from aio_pika.message import IncomingMessage
import asyncio
import aio_pika
from aio_pika.channel import Channel
from aio_pika.queue import Queue
from motor.motor_asyncio import AsyncIOMotorClient
from injector.config import Config
from json import loads


class CWEConsumer(RabbitMQConsumer):
    def __init__(
        self,
        queue: Queue,
        db_client: AsyncIOMotorClient,
    ):
        self.feed_type = "CWE"
        self.db = db_client.vulnerabilities
        self.collection = self.db.cwe
        super().__init__(queue=queue, db_client=db_client)

    async def process_message(self, orig_message: IncomingMessage):
        data = loads(orig_message.body.decode())
        document = data["doc"]
        collection = data["collection"]
        await self.db[collection].insert_one(document)


async def _prepare_consumed_queue(channel: Channel) -> Queue:
    queue = await channel.declare_queue(
        name="CWE",
    )
    await queue.bind(exchange="test-exchange", routing_key="CWE")
    return queue


async def main(consumer_class) -> None:
    mongo_db_client = AsyncIOMotorClient(
        f"mongodb://{Config.getMongoHost()}:{Config.getMongoPort()}"
    )
    rabbitmq_connection = await aio_pika.connect_robust(
        loop=loop,
        url=f"amqp://{Config.getRabbitUser()}:{Config.getRabbitPass()}@{Config.getRabbitHost()}/",
    )

    try:
        async with rabbitmq_connection.channel() as channel:
            await channel.set_qos(prefetch_count=100)

            queue = await _prepare_consumed_queue(channel)

            consumer = consumer_class(
                queue=queue,
                db_client=mongo_db_client,
            )

            await consumer.consume()
    finally:
        await rabbitmq_connection.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(CWEConsumer))
    loop.close()
