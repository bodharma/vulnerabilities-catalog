from loguru import logger
from xml.sax import make_parser
from harvester.handlers.XMLHandler import XMLFileHandler
from harvester.handlers.JSONHandler import JSONFileHandler
from harvester.handlers.content_handler import CWEHandler
from shutil import rmtree
from harvester.config import Config
import json


class CWEDownloads(XMLFileHandler):
    def __init__(self):
        self.feed_type = "CWE"
        super().__init__(self.feed_type)

        self.feed_url = Config.getFeedURL(self.feed_type.lower())

        self.logger = logger

        # make parser
        self.parser = make_parser()
        self.ch = CWEHandler()
        self.parser.setContentHandler(self.ch)

    def file_content_to_queue(self, file_tuple):
        working_dir, filename = file_tuple

        self.parser.parse(filename)
        x = 0
        for cwe in self.ch.cwe:
            try:
                cwe["related_weaknesses"] = list(set(cwe["related_weaknesses"]))
            except KeyError:
                pass
            self.process_item(cwe)
            x += 1

        self.logger.debug("Processed {} entries from file: {}".format(x, filename))

        try:
            self.logger.debug("Removing working dir: {}".format(working_dir))
            rmtree(working_dir)
        except Exception as err:
            self.logger.error(
                "Failed to remove working dir; error produced: {}".format(err)
            )


class CVEDownloads(JSONFileHandler):
    def __init__(self):
        self.feed_type = "CVES"
        self.prefix = "CVE_Items.item"
        self.api_key = Config.getApiKey()
        super().__init__(
            feed_type=self.feed_type, prefix=self.prefix, api_key=self.api_key
        )

        self.feed_url = Config.getFeedURL("cve")

        self.logger = logger

    def process_items(self, items):
        self.queue.publish(messages=[json.dumps(item) for item in items])

    def process_publish_local_file(self, files):
        _, filename = files
        json_file = open(filename, "r")
        json_data = json.load(json_file)
        if "vulnerabilities" not in json_data.keys():
            raise KeyError("Invalid JSON file: vulnerabilities key not found")
        self.process_items(json_data["vulnerabilities"])


class EPSSDownloads(JSONFileHandler):
    def __init__(self):
        self.feed_type = "EPSS"
        self.prefix = "EPSS_Items.item"
        super().__init__(feed_type=self.feed_type, prefix=self.prefix)

        self.feed_url = Config.getFeedURL("epss")

        self.logger = logger

    def process_items(self, items):
        self.queue.publish(messages=[json.dumps(item) for item in items])

    def process_publish_local_file(self, files):
        _, filename = files
        json_file = open(filename, "r")
        json_data = json.load(json_file)
        if "data" not in json_data.keys():
            raise KeyError("Invalid JSON file: vulnerabilities key not found")
        self.process_items(json_data["data"])
