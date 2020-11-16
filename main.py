import datetime
import os
import logging
from os.path import join, dirname
from dotenv import load_dotenv

from binalerter import BinAlerter
from yamlscheduler import YamlScheduler
from pushover import Pushover

def CheckBinDay(pushOverArgs):
    
    message = None
    try:
        alerter = BinAlerter()
        alerter.GetNextBinDay()
    except Exception as e:
        message = e
        alerter = None
        logging.exception("CheckBinDay(): " + message)
    
    if not pushOverArgs is None:
        Pushover.Initialise(pushOverArgs[0], pushOverArgs[1])  

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
        logging.info('===== START =====')
        logging.basicConfig(filename="yamlscheduler.log", filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

        dotenv_path = join(dirname(__file__), '.env')
        load_dotenv(dotenv_path+"(")
        if not os.getenv('PUSHOVER_USER_KEY') is None:
            pushOverArgs = [os.getenv('PUSHOVER_USER_KEY'), os.getenv('PUSHOVER_APP_TOKEN')]
        else:
            pushOverArgs = None
        sch = YamlScheduler()
        YamlScheduler.Initialise(logging, CheckBinDay, pushOverArgs)
        YamlScheduler.Wait()
        logging.info('===== END =====')

    except Exception as e:
        logging.exception("mail(): " + e)
    finally:
        logging.info("Done")

if __name__ == '__main__':
    main()