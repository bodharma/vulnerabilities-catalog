from harvester.handlers.DownloadHandler import DownloadHandler
from abc import abstractmethod
import json


class XMLFileHandler(DownloadHandler):
    def __init__(self, feed_type):
        super().__init__(feed_type)
        self.is_update = True

    def __repr__(self):
        """return string representation of object"""
        return "<< XMLFileHandler:{} >>".format(self.feed_type)

    def process_item(self, item):
        message = {"collection": self.feed_type.lower(), "doc": item}
        self.queue.publish(
            messages=[json.dumps(message)],
        )
