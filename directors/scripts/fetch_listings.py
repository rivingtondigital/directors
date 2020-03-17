# from crontab import Crontab()

import logging
from directors import settings
from time import sleep
from directors.util import market_tickers

logger = logging.getLogger(settings.APP)


for i in range(1000):
    logger.debug("This is a logged at lvl DEBUG: {}".format(logger.name))
    logger.info("This is a logged at lvl INFO")
    logger.warning("This is a logged at lvl WARN")
    logger.error("This is logged at lvl ERROR")
    logger.critical("This is logged at lvl CRITICAL")
    sleep(2)
