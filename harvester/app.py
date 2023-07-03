from harvester.processors.sources_processor import (
    CVEDownloads,
    CWEDownloads,
    EPSSDownloads,
)


def cwe():
    cwd = CWEDownloads()

    files = cwd.download_store_temp(cwd.feed_url)
    cwd.file_content_to_queue(files)


def cve():
    cve = CVEDownloads()
    files = cve.download_store_temp(cve.feed_url)
    cve.process_publish_local_file(files)


def epss():
    epss = EPSSDownloads()
    files = epss.download_store_temp(epss.feed_url)
    epss.process_publish_local_file(files)


if __name__ == "__main__":
    cwe()
    cve()
    epss()
