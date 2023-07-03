import zipfile
from abc import ABC, abstractmethod
from loguru import logger
from harvester.config import Config
from requests import adapters, Session
from urllib3 import Retry
import threading
import tqdm
import time
import os
import tempfile
from io import BytesIO
import gzip
import sys
from shutil import copy
from dateutil.parser import parse as parse_datetime
from harvester.rabbit.rabbit_queue import RabbitMQ

thread_local = threading.local()


class DownloadHandler(ABC):
    """
    DownloadHandler is the base class for all downloads and subsequent processing of the downloaded content.
    Each download script has a derived class which handles specifics for that type of content / download.
    """

    def __init__(self, feed_type, prefix=None, api_key=None):
        self._end = None
        self.api_key = api_key

        self.feed_type = feed_type

        self.prefix = prefix

        self.queue = RabbitMQ(queue=self.feed_type)

        self.queue.flush()
        self.progress_bar = None

        self.last_modified = None

        self.do_process = True

        self.logger = logger

        self.config = Config()

    def __repr__(self):
        """return string representation of object"""
        return "<< DownloadHandler:{} >>".format(self.feed_type)

    def get_session(
        self,
        retries=3,
        backoff_factor=0.3,
        status_forcelist=(429, 500, 502, 503, 504),
        session=None,
    ):
        """
        Method for returning a session object per every requesting thread
        """

        if not hasattr(thread_local, "session"):
            session = session or Session()
            retry = Retry(
                total=retries,
                read=retries,
                connect=retries,
                backoff_factor=backoff_factor,
                status_forcelist=status_forcelist,
            )

            adapter = adapters.HTTPAdapter(max_retries=retry)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            thread_local.session = session

        return thread_local.session

    def _handle_queue_progressbar(self, description):
        """
        Method for handling the progressbar during queue processing

        :param description: Description for tqdm progressbar
        :type description: str
        """
        max_len = self.queue.qsize()

        pbar = tqdm(total=max_len, desc=description)
        not_Done = True
        q_len = max_len
        dif_old = 0
        x = 0

        while not_Done:
            current_q_len = self.queue.qsize()

            if x % 10 == 0:
                # log stats the first cycle and every 10th cycle thereafter
                self.logger.debug(
                    "Queue max_len: {}, current_q_len: {}, q_len: {}, dif_old: {}, cycle: {}".format(
                        max_len, current_q_len, q_len, dif_old, x
                    )
                )

            if current_q_len != 0:
                if current_q_len != q_len:
                    q_len = current_q_len
                    dif = max_len - q_len

                    pbar.update(int(dif - dif_old))

                    dif_old = dif
            else:
                pbar.update(int(max_len - dif_old))
                not_Done = False

            x += 1
            time.sleep(5)

        self.logger.debug(
            "Queue max_len: {}, q_len: {}, dif_old: {}, cycles: {}".format(
                max_len, q_len, dif_old, x
            )
        )

        pbar.close()

    def store_file(self, response_content, content_type, url):
        """
        Method to store the download based on the headers content type

        :param response_content: Response content
        :type response_content: bytes
        :param content_type: Content type; e.g. 'application/zip'
        :type content_type: str
        :param url: Download url
        :type url: str
        :return: A working directory and a filename
        :rtype: str and str
        """
        wd = tempfile.mkdtemp()
        filename = None

        if (
            content_type == "application/zip"
            or content_type == "application/x-zip"
            or content_type == "application/x-zip-compressed"
            or content_type == "application/zip-compressed"
        ):
            filename = os.path.join(wd, url.split("/")[-1][:-4])
            self.logger.debug("Saving file to: {}".format(wd))

            with zipfile.ZipFile(BytesIO(response_content)) as zip_file:
                zip_file.extractall(wd)

        elif (
            content_type == "application/x-gzip"
            or content_type == "application/gzip"
            or content_type == "application/x-gzip-compressed"
            or content_type == "application/gzip-compressed"
        ):
            filename = os.path.join(wd, url.split("/")[-1][:-3])
            self.logger.debug("Saving file to: {}".format(wd))

            buf = BytesIO(response_content)
            with open(filename, "wb") as f:
                f.write(gzip.GzipFile(fileobj=buf).read())

        elif "application/json" in content_type or "application/xml" in content_type:
            if "cve" in url:
                filename = os.path.join(wd, "cve.json")
            else:
                filename = os.path.join(wd, url.split("/")[-1])
            self.logger.debug("Saving file to: {}".format(wd))

            with open(filename, "wb") as output_file:
                output_file.write(response_content)

        elif content_type == "application/local":
            filename = os.path.join(wd, url.split("/")[-1])
            self.logger.debug("Saving file to: {}".format(wd))

            copy(url[7:], filename)

        else:
            self.logger.error(
                "Unhandled Content-Type encountered: {} from url".format(
                    content_type, url
                )
            )
            sys.exit(1)

        return wd, filename

    def download_send_wd_file_to_queue(self, file_tuple):
        wd, filename = file_tuple
        if filename is not None:
            self.file_queue.publish((wd, filename))
        else:
            self.logger.error(
                "Unable to retrieve a filename; something went wrong when trying to save the file"
            )
            sys.exit(1)

    def download_store_temp(self, url):
        self.logger.debug("Downloading from url: {}".format(url))
        session = self.get_session()
        try:
            headers = None
            if self.api_key:
                headers = {"api": self.api_key}
            with session.get(url, headers=headers) as response:
                try:
                    self.last_modified = parse_datetime(
                        response.headers["last-modified"], ignoretz=True
                    )
                except KeyError:
                    self.logger.error(
                        "Did not receive last-modified header in the response; setting to default "
                        "(01-01-1970) and force update! Headers received: {}".format(
                            response.headers
                        )
                    )
                    # setting to last_modified to default value
                    self.last_modified = parse_datetime("01-01-1970")

                self.logger.debug(
                    "Last {} modified value: {} for URL: {}".format(
                        self.feed_type, self.last_modified, url
                    )
                )
                content_type = response.headers["content-type"]

                self.logger.debug(
                    "URL: {} fetched Content-Type: {}".format(url, content_type)
                )

                wd, filename = self.store_file(
                    response_content=response.content,
                    content_type=content_type,
                    url=url,
                )
                if not os.path.exists(filename):
                    files_list = os.listdir(wd)
                    if len(files_list) == 1:
                        filename = os.path.join(wd, files_list[0])
                return wd, filename
        except Exception as err:
            self.logger.info(
                "Exception encountered during download from: {}. Please check the logs for more information!".format(
                    url
                )
            )
            self.logger.error(
                "Exception encountered during the download from: {}. Error encountered: {}".format(
                    url, err
                )
            )


@abstractmethod
def process_item(self, **kwargs):
    raise NotImplementedError


@abstractmethod
def file_to_queue(self, *args):
    raise NotImplementedError
