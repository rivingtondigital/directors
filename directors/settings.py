import logging
from logging.handlers import TimedRotatingFileHandler
import os
import zlib

APP = 'directors'
LOG_FILE = '/home/jovyan/work/data/logs/directors.log'


def namer(name):
    return name + ".gz"


def rotator(source, dest):
    with open(source, "rb") as sf:
        data = sf.read()
        compressed = zlib.compress(data, 9)
        with open(dest, "wb") as df:
            df.write(compressed)
    os.remove(source)

class JsonFormatter(logging.Formatter):



logger = logging.getLogger(APP)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

logger.info(">>>>>>>>>> Logging Initialized! <<<<<<<<<")


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)



rotate_handler = TimedRotatingFileHandler(
    LOG_FILE,
    when='m',
    interval=1,
    backupCount=20
)

rotate_handler.setLevel(logging.INFO)
rotate_handler.setFormatter(formatter)

rotate_handler.rotator = rotator
rotate_handler.namer = namer

logger.addHandler(rotate_handler)


