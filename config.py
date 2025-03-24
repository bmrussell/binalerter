import confuse
import os

class Timing:

    def __init__(self, day, time) -> None:
        self.Day = day
        self.Time = time

class Config:
    def __init__(self):  
        confuseConfig = confuse.Configuration('BinAlerter')

        self.CalendarUrl = confuseConfig['scrape']['calendar_url'].get()
        self.AddressUrl = confuseConfig['scrape']['address_url'].get()
        self.CollectionUrl = confuseConfig['scrape']['collection_url'].get()
        
        self.Postcode = confuseConfig['location']['postcode'].get()
        self.Address = confuseConfig['location']['address'].get()
        
        self.PushoverToken = confuseConfig['pushover']['apptoken'].get()
        self.PushoverKey = confuseConfig['pushover']['userkey'].get()

        self.Loglevel = confuseConfig['app']['logLevel'].get()
        self.Logfile = os.path.join(confuseConfig.config_dir(), "BinAlerter.log")

        self.Timings = []
        for t in confuseConfig['schedule']:
            self.Timings.append(Timing(t['day'].get(), t['time'].get()))
