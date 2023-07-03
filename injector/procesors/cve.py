from injector.rabbit.rabbit_queue import RabbitMQ
from injector.db.mongoHandler import Mongo


class CVE(RabbitMQ, Mongo):
    def __init__(self):
        self.feed_type = "CVE"
        RabbitMQ.__init__(self, queue=self.feed_type)
        Mongo.__init__(self, db_name="vulnerabilities", collection_name=self.feed_type)
