import asyncio
from abc import abstractmethod, ABC
from aio_pika.message import IncomingMessage
from aio_pika.queue import Queue


async def mark_message_processed(orig_message: IncomingMessage):
    """Notify message broker about message being processed."""
    try:
        await orig_message.ack()
    except Exception:
        await orig_message.nack()
        raise


class RabbitMQConsumer(ABC):
    """RabbitMQ consumer abstract class responsible for consuming data from the queue."""

    def __init__(
        self,
        queue: Queue,
        iterator_timeout: int = 5,
        iterator_timeout_sleep: float = 5.0,
        *args,
        **kwargs,
    ):
        """
        Args:
            queue (Queue): aio_pika queue object
            iterator_timeout (int): In seconds.
                The queue iterator raises TimeoutError if no message comes for this time and iterating starts again.
            iterator_timeout_sleep (float): In seconds. Time for sleeping between attempts of iterating.
        """
        self.queue = queue
        self.iterator_timeout = iterator_timeout
        self.iterator_timeout_sleep = iterator_timeout_sleep

        self.consuming_flag = True

    async def consume(self):
        """Consumes data from RabbitMQ queue forever until `stop_consuming()` is called."""
        async with self.queue.iterator(timeout=self.iterator_timeout) as queue_iterator:
            while self.consuming_flag:
                try:
                    async for orig_message in queue_iterator:
                        await self.process_message(orig_message)

                        if not self.consuming_flag:
                            break  # Breaks the queue iterator
                except asyncio.exceptions.TimeoutError:
                    await self.on_finish()
                    if self.consuming_flag:
                        await asyncio.sleep(self.iterator_timeout_sleep)
                finally:
                    await self.on_finish()

    @abstractmethod
    async def process_message(self, orig_message: IncomingMessage):
        raise NotImplementedError()

    def stop_consuming(self):
        """Stops the consuming gracefully"""
        self.consuming_flag = False

    async def on_finish(self):
        """Called after the message consuming finished."""
        pass
