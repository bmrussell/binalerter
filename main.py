import datetime
import os
import time
import logging
import schedule
from os.path import join, dirname

from binalerter import BinAlerter
from pushover import Pushover
from config import Config

gbConfig = Config()

def CheckBinDay():
    
    message = None
    try:
        alerter = BinAlerter(gbConfig)
        alerter.GetNextBinDay()
    except Exception as e:
        message = str(e)
        alerter = None
        logging.exception("CheckBinDay(): " + message)
    
    if not gbConfig.pushover_userkey is None:
        Pushover.Initialise(gbConfig.pushover_userkey, gbConfig.pushover_apptoken)  

        if alerter is None:
            message = "Failed: " + message
        else:
            message = "Put \n"
            for bin in alerter.Collecting:
                    message = message + bin + "\n"
            message = message + "out on " + alerter.NextCollection.strftime('%d %B %Y') + "."
            logging.info(message)

        Pushover.Notify(message, "bugle")
    

def main() -> None:
    try:        
        l = logging.DEBUG
        if gbConfig.loglevel == "WARN":
            l = logging.WARN
        logging.basicConfig(filename=gbConfig.logfile, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=l)
        logging.info('===== START =====')

        getattr(schedule.every(), gbConfig.schedule_day).at(gbConfig.schedule_time).do(CheckBinDay)
        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception as e:
        logging.exception("mail(): " + str(e))
    finally:
        logging.info("Done")
        logging.info('===== END =====')

if __name__ == '__main__':
    main()