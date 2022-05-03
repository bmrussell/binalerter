import datetime
import os
import logging
import requests
import json
from config import Config

from os.path import join, dirname
from time import strptime

from bs4 import BeautifulSoup
from urllib.request import urlopen

from pushover import Pushover

class BinAlerter:
    def __init__(self, config):
        """
        Constructor
            1. Read Configuration from YAML file
            2. initialise class variables
            3. Initialise logging            
        """
        
        self.NextCollection = None
        self.Collecting = []
        self.config = config


        logging.debug("BinAlerter:__init__ logging level " + self.config.Loglevel)


    def GetBinPage(self, session):
        # Hit the collections web page, gimme cookie
        logging.debug("BinAlerter.GetBinPage()")
        request = requests.Request('GET',self.config.CalendarUrl)
        prepared = request.prepare()
        response = session.send(prepared)
        logging.debug(f"Response HTTP:{response.status_code}")

    def GetNextBinDay(self):

        logging.debug("BinAlerter.GetNextBinDay()")
        session = requests.Session()
        logging.debug("Opened session")

        self.GetBinPage(session)

        # Find addresses for the postcode and year/month (for some reason)
        rightNow = datetime.datetime.now()
        binMonth = rightNow.month
        binYear = rightNow.year
        binDay = rightNow.day   
        params = {'Postcode': self.config.Postcode, 'Month': binMonth, 'Year': binYear}
        r = requests.post(self.config.AddressUrl, data=params)
        addressJson = json.loads(r.text)

        # Loop through the JSON response and find the address that matches the first line
        # from config
        # Grab the UPRN value to post back as a unique id for that address
        for address in addressJson["Model"]["PostcodeAddresses"]:
            if address["AddressLine1"] == self.config.Address:
                uprn =  address["UPRN"]
                break

        # Get the calendar for the current month
        # All being well we'll just look for the next date in that calendar that's flagged as a collection day
        # If there is no date in this month after today, we'll need to pull the next months calendar and take the first 
        # collection day from next month

        params = {'Month': binMonth, 'Year': binYear, 'Postcode': self.config.Postcode, 'Uprn': uprn}
        r = requests.post(self.config.CollectionUrl, data=params)
        
        soup = BeautifulSoup(r.text, 'html.parser')
        # Calendar <a> elements are the following class values for data-event-id:
        #   pod     Mixed dry recycling (blue lidded bin) and glass (black box or basket)
        #   res     Household waste
        #   cgw     Chargeable garden waste
        
        collectionDays = soup.find_all('a', {'data-event-id':{'pod','res','cgw'}})

        logging.debug("Got the collection days")

        iBinKind = 0
        for collectionDay in collectionDays:
            # Parse date in format "Monday 11 May, 2020"
            collectionTime = strptime(collectionDay["data-original-datetext"], "%A %d %B, %Y")
            collectionDate = datetime.datetime(collectionTime.tm_year, collectionTime.tm_mon, collectionTime.tm_mday)

            # We found the next collection day
            if collectionDate > rightNow:
                if self.NextCollection is None:
                    self.NextCollection = collectionDate
                    logging.info(f"Found next bin day: {self.NextCollection.strftime('%d %B %Y')}")

            # While we have the next collection day collect the next bin type
            if (not self.NextCollection is None) and self.NextCollection == collectionDate:
                self.Collecting.append(collectionDay["data-original-title"])
                iBinKind = iBinKind + 1
            
            # Exit out if gone past the next collection day
            # cos we're done
            if (not self.NextCollection is None) and collectionDate > self.NextCollection:
                break
        
        logging.debug("Done")
