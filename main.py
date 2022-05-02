import datetime
import os
import time
import logging
import schedule
from os.path import join, dirname, exists
from dotenv import load_dotenv
from pathlib import Path

from binalerter import BinAlerter
from pushover import Pushover
from config import Config, Timing

if exists('config/test.env'):
    dotenv_path = Path('config/test.env')
    load_dotenv(dotenv_path=dotenv_path)
    print(f'Using environement from {dotenv_path}')
    binalerterdir = os.getenv('BINALERTERDIR')
    print(f'BINALERTERDIR={binalerterdir}')
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
    
    if not gbConfig.PushoverKey is None:
        Pushover.Initialise(gbConfig.PushoverKey, gbConfig.PushoverToken)  

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
        if gbConfig.Loglevel == "WARN":
            l = logging.WARN
        
        fmt = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(filename=gbConfig.Logfile,      # Log out to file
                            format=fmt,
                            level=l)
        
        console = logging.StreamHandler()                   # and also onsole
        console.setLevel(l)
        formatter = logging.Formatter(fmt)
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)           # add the handler to the root logger

        logging.info('===== START =====')
        CheckBinDay()
        for t in gbConfig.Timings:
            logging.info(f'Checking every {t.Day} at {t.Time}')
            getattr(schedule.every(), t.Day).at(t.Time).do(CheckBinDay)

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
