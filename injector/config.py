import configparser
import os

import pymongo
from urllib import parse
from datetime import datetime
import pika


class Config:
    ConfigParser = configparser.ConfigParser()

    default = {
        "rabbitHost": "localhost",
        "rabbitPort": 5672,
        "rabbitQ": "test-queue",
        "rabbitExchange": "test-exchange",
        "rabbitPass": "guest",
        "rabbitUser": "guest",
        "mongoHost": "localhost",
        "mongoPort": 27017,
        "mongoDB": "cvedb",
        "mongoUsername": "guest",
        "mongoPassword": "guest",
        "mongoSrv": False,
        "mongoAuth": "admin",
    }

    CVE_NVD_API_KEY = os.environ.get("CVE_NVD_API_KEY", "")

    sources = {
        "cve": "https://services.nvd.nist.gov/rest/json/cves/2.0/?pubStartDate=2023-01-04T00:00:00.000&pubEndDate=2023-02-22T00:00:00.000",
        "cwe": "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip",
        "epss": "https://api.first.org/data/v1/epss",
        "includecve": True,
        "includecwe": True,
        "includeepss": True,
    }

    @classmethod
    def readSetting(cls, section, item, default):
        result = default
        try:
            if type(default) == bool:
                result = cls.ConfigParser.getboolean(section, item)
            elif type(default) == int:
                result = cls.ConfigParser.getint(section, item)
            else:
                result = cls.ConfigParser.get(section, item)
        except:
            pass
        return result

    @classmethod
    def getFeedURL(cls, source):
        return cls.readSetting("Sources", source, cls.sources.get(source, ""))

    @classmethod
    def includesFeed(cls, feed):
        return cls.readSetting(
            "EnabledFeeds", feed, cls.sources.get("include" + feed, False)
        )

    @classmethod
    def getApiKey(cls):
        return cls.readSetting("CVE", "NVD_API_KEY", cls.CVE_NVD_API_KEY)

    @classmethod
    def getMongoConnection(cls):
        mongoSrv = cls.readSetting("Database", "DnsSrvRecord", cls.default["mongoSrv"])
        mongoHost = cls.readSetting("Database", "Host", cls.default["mongoHost"])
        mongoPort = cls.readSetting("Database", "Port", cls.default["mongoPort"])
        mongoAuth = cls.readSetting("Database", "AuthDB", cls.default["mongoAuth"])
        mongoDB = cls.getMongoDB()
        mongoUsername = parse.quote(
            cls.readSetting("Database", "Username", cls.default["mongoUsername"])
        )
        mongoPassword = parse.quote(
            cls.readSetting("Database", "Password", cls.default["mongoPassword"])
        )
        if mongoUsername and mongoPassword and mongoSrv is True:
            mongoURI = "mongodb+srv://{username}:{password}@{host}/{db}?authSource={auth}&retryWrites=true&w=majority".format(
                username=mongoUsername,
                password=mongoPassword,
                host=mongoHost,
                db=mongoDB,
                auth=mongoAuth,
            )
        elif mongoUsername and mongoPassword:
            mongoURI = "mongodb://{username}:{password}@{host}:{port}/{db}?authSource={auth}".format(
                username=mongoUsername,
                password=mongoPassword,
                host=mongoHost,
                port=mongoPort,
                db=mongoDB,
                auth=mongoAuth,
            )
        else:
            mongoURI = "mongodb://{host}:{port}/{db}".format(
                host=mongoHost, port=mongoPort, db=mongoDB
            )
        connect = pymongo.MongoClient(mongoURI, connect=False)
        return connect[mongoDB]

    @classmethod
    def getMongoDB(cls):
        return cls.readSetting("Database", "DB", cls.default["mongoDB"])

    @classmethod
    def getRabbitHost(cls):
        return cls.readSetting("Rabbit", "Host", cls.default["rabbitHost"])

    @classmethod
    def getRabbitPort(cls):
        return cls.readSetting("Rabbit", "Port", cls.default["rabbitPort"])

    @classmethod
    def getRabbitCreds(cls):
        rabbitPass = cls.readSetting("Rabbit", "Password", cls.default["rabbitPass"])
        rabbitUser = cls.readSetting("Rabbit", "Username", cls.default["rabbitUser"])
        return pika.PlainCredentials(rabbitUser, rabbitPass)

    @classmethod
    def getRabbitConnection(cls):
        rabbitHost = cls.getRabbitHost()
        rabbitPort = cls.getRabbitPort()
        rabbitCreds = cls.getRabbitCreds()
        return pika.BlockingConnection(
            pika.ConnectionParameters(
                host=rabbitHost,
                port=rabbitPort,
                credentials=rabbitCreds,
            )
        )

    @classmethod
    def getRabbitQueue(cls):
        return cls.readSetting("Rabbit", "rabbitQ", cls.default["rabbitQ"])

    @classmethod
    def getRabbitExchange(cls):
        return cls.readSetting(
            "Rabbit", "rabbitExchange", cls.default["rabbitExchange"]
        )

    @classmethod
    def declareExchange(cls, channel, exchange: str):
        return channel.exchange_declare(exchange=exchange, exchange_type="topic")
