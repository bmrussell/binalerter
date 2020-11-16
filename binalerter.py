import datetime
import confuse
import os
import logging
import requests
import json
from os.path import join, dirname
from dotenv import load_dotenv

from bs4 import BeautifulSoup
from urllib.request import urlopen
from time import strptime

from yamlscheduler import YamlScheduler
from pushover import Pushover

class Config:
    def __init__(self, url, address_url, collection_url, postcode, address, token, clients):
        self.calendar_url = url
        self.address_url = address_url
        self.collection_url = collection_url
        self.postcode = postcode
        self.address = address
        self.apitoken = token
        self.clients = clients

class BinAlerter:
    def __init__(self):
        """
        Constructor
            1. Read Configuration from YAML file
            2. initialise class variables
            3. Initialise logging            
        """
        
        self.NextCollection = None
        self.Collecting = []
        
        config = confuse.Configuration('BinAlerter')
        self.config = config

        logLevel = config['logLevel'].get()
        if logLevel == "DEBUG":
            l = logging.DEBUG
        elif logLevel == "WARN":
            l = logging.WARN

        logfileName = os.path.join(config.config_dir(), "BinAlerter.log")
        logging.basicConfig(filename=logfileName, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=l)
        logging.debug("BinAlerter:__init__ logging level " + logLevel)

        self.config = Config(   config['scrape']['calendar_url'].get(),
                                config['scrape']['address_url'].get(),
                                config['scrape']['collection_url'].get(),
                                config['location']['postcode'].get(),
                                config['location']['address'].get(),
                                config['pushover']['api_token'].get(),
                                config['pushover']['clients'].get(),
                            )

    def GetBinPage(self, session):
        # Hit the collections web page, gimme cookie
        logging.debug("BinAlerter.GetBinPage()")
        getLoginFormheaders = { 'Host': 'secure.tesco.com',
                        'Connection': 'keep-alive',
                        'DNT': '1',
                        'Upgrade-Insecure-Requests': '1',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Dest': 'document',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8'         
                    }
        request = requests.Request('GET',self.config.calendar_url)
        prepared = request.prepare()
        response = session.send(prepared)
        logging.debug("\tHTTP{}", response.status_code)

    def GetNextBinDay(self):

        logging.debug("BinAlerter.GetNextBinDay()")
        session = requests.Session()
        logging.debug("\tOpened session")

        self.GetBinPage(session)

        # Find addresses for the postcode and year/month (for some reason)
        rightNow = datetime.datetime.now()
        binMonth = rightNow.month
        binYear = rightNow.year
        binDay = rightNow.day   
        params = {'Postcode': self.config.postcode, 'Month': binMonth, 'Year': binYear}
        r = requests.post(self.config.address_url, data=params)
        addressJson = json.loads(r.text)

        # Loop through the JSON response and find the address that matches the first line
        # from config
        # Grab the UPRN value to post back as a unique id for that address
        for address in addressJson["Model"]["PostcodeAddresses"]:
            if address["AddressLine1"] == self.config.address:
                uprn =  address["UPRN"]
                break

        # Get the calendar for the current month
        # All being well we'll just look for the next date in that calendar that's flagged as a collection day
        # If there is no date in this month after today, we'll need to pull the next months calendar and take the first 
        # collection day from next month

        params = {'Month': binMonth, 'Year': binYear, 'Postcode': self.config.postcode, 'Uprn': uprn}
        r = requests.post(self.config.collection_url, data=params)
        
        soup = BeautifulSoup(r.text, 'html.parser')
        # Calendar <a> elements are the following class values for data-event-id:
        #   pod     Mixed dry recycling (blue lidded bin) and glass (black box or basket)
        #   res     Household waste
        #   cgw     Chargeable garden waste
        
        collectionDays = soup.find_all('a', {'data-event-id':{'pod','res','cgw'}})
        iBinKind = 0
        for collectionDay in collectionDays:
            # Parse date in format "Monday 11 May, 2020"
            collectionTime = strptime(collectionDay["data-original-datetext"], "%A %d %B, %Y")
            collectionDate = datetime.datetime(collectionTime.tm_year, collectionTime.tm_mon, collectionTime.tm_mday)

            # We found the next collection day
            if collectionDate > rightNow:
                if self.NextCollection is None:
                    self.NextCollection = collectionDate
                    logging.debug("Found next bin day" + self.NextCollection.strftime('%d %B %Y'))

            # While we have the next collection day collect the next bin type
            if (not self.NextCollection is None) and self.NextCollection == collectionDate:
                self.Collecting.append(collectionDay["data-original-title"])
                iBinKind = iBinKind + 1
            
            # Exit out if gone past the next collection day
            if (not self.NextCollection is None) and collectionDate > self.NextCollection:
                break
        
        logging.debug("\tDone")
