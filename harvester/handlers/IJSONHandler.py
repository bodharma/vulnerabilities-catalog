import ijson
from loguru import logger


class IJSONHandler(object):
    def __init__(self):
        self.logger = logger

    def fetch(self, filename, prefix):
        x = 0
        with open(filename, "rb") as input_file:
            for item in ijson.items(input_file, prefix):
                yield item
                x += 1

        self.logger.debug(
            "Processed {} items from file: {}, using prefix: {}".format(
                x, filename, prefix
            )
        )
