from injector.rabbit.rabbit_queue import RabbitMQ
from injector.db.mongoHandler import Mongo


class EPSS(RabbitMQ, Mongo):
    def __init__(self):
        self.feed_type = "EPSS"
        RabbitMQ.__init__(self, queue=self.feed_type)
        Mongo.__init__(self, db_name="vulnerabilities", collection_name=self.feed_type)
