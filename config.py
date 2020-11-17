import confuse
import os

class Config:
    def __init__(self):  
        #dir = confuse.Configuration.config_dir(),      
        confuseConfig = confuse.Configuration('BinAlerter')
        
        self.calendar_url = confuseConfig['scrape']['calendar_url'].get()
        self.address_url = confuseConfig['scrape']['address_url'].get()
        self.collection_url = confuseConfig['scrape']['collection_url'].get()
        
        self.postcode = confuseConfig['location']['postcode'].get()
        self.address = confuseConfig['location']['address'].get()
        
        self.pushover_apptoken = confuseConfig['pushover']['apptoken'].get()
        self.pushover_userkey = confuseConfig['pushover']['userkey'].get()

        self.loglevel = confuseConfig['app']['logLevel'].get()
        self.logfile = os.path.join(confuseConfig.config_dir(), "BinAlerter.log")

        self.schedule_day = confuseConfig['schedule']['day'].get()
        self.schedule_time = confuseConfig['schedule']['time'].get()        