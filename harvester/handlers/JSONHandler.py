from harvester.handlers.DownloadHandler import DownloadHandler
from harvester.handlers.IJSONHandler import IJSONHandler


class JSONFileHandler(DownloadHandler):
    def __init__(self, feed_type, prefix, api_key=None):
        self.api_key = api_key
        super().__init__(feed_type=feed_type, api_key=api_key)

        self.prefix = prefix
        self.ijson_handler = IJSONHandler()

    def __repr__(self):
        """return string representation of object"""
        return "<< JSONFileHandler:{} >>".format(self.feed_type)
