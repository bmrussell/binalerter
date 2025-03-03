import datetime
import requests
import json
import confuse
from os.path import join, dirname
from time import strptime
from bs4 import BeautifulSoup
from urllib.request import urlopen
import http.client, urllib

def printlog(message):
    t = datetime.datetime.now().strftime(f'%d/%M/%Y %H:%M:%S')
    print(f'{t}\t{message}')

def main() -> None:
    # Get parameters
    today = datetime.datetime.now().date()
    tomorrow = today + datetime.timedelta(days=1)
    printlog('Started')

    confuseConfig = confuse.Configuration('BinAlerter', __name__)
    confuseConfig.set_file('config.yaml')
    
    calendar_url = None
    calendar_url = confuseConfig['scrape']['calendar_url'].get()
    address_url = confuseConfig['scrape']['address_url'].get()
    collection_url = confuseConfig['scrape']['collection_url'].get()
    postcode = confuseConfig['location']['postcode'].get()
    addressline = confuseConfig['location']['address'].get()
    pushoverToken = confuseConfig['pushover']['apptoken'].get()
    pushoverKey = confuseConfig['pushover']['userkey'].get()

    if calendar_url != None:
        printlog('Got config')
    else:
        printlog('Failed to get config')
        exit()

    # Get the bin page
    session = requests.Session()
    getLoginFormheaders = {
        'Host': 'ilforms.wiltshire.gov.uk',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Dest': 'document',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8',
    }
    request = requests.Request('GET', calendar_url)
    prepared = request.prepare()
    response = session.send(prepared)

    printlog('Got calendar')

    # Find addresses for the postcode and year/month (for some reason)
    params = {'Postcode': postcode, 'Month': today.month, 'Year': today.year}
    r = requests.post(address_url, data=params)
    addressJson = json.loads(r.text)

    # Select our address
    uprn = None
    for address in addressJson['Model']['PostcodeAddresses']:
        if address['AddressLine1'] == addressline:
            uprn = address['UPRN']
            break

    if uprn == None:
        printlog(f'Failed to get uprn')
        exit()

    printlog(f'Got uprn={uprn}')

    # Get the collection calendar
    params = {'Month': today.month, 'Year': today.year, 'Postcode': postcode, 'Uprn': uprn}
    r = requests.post(collection_url, data=params)
    soup = BeautifulSoup(r.text, 'html.parser')
    collectionDays = soup.find_all('a', {'data-event-id': {'pod', 'res', 'cgw'}})

    printlog(f'Got {len(collectionDays)} collection days')

    # See if the next collection is tomorrow
    collection = None
    for collectionDay in collectionDays:
        # Parse date in format 'Monday 11 May, 2020'
        collectionTime = strptime(collectionDay['data-original-datetext'], '%A %d %B, %Y')
        collectionDate = datetime.datetime(
            collectionTime.tm_year, collectionTime.tm_mon, collectionTime.tm_mday
        ).date()

        if collectionDate == tomorrow:
            collection = collectionDay['data-original-title']
            break

    # Send alert if the collection was found to be tomorrow
    if collection != None:
        printlog(f'Collection tomorrow')
        conn = http.client.HTTPSConnection('api.pushover.net:443')
        conn.request(
            'POST',
            '/1/messages.json',
            urllib.parse.urlencode(
                {
                    'token': f'{pushoverToken}',
                    'user': f'{pushoverKey}',
                    'message': f'Put {collection} out tonight',
                }
            ),
            {'Content-type': 'application/x-www-form-urlencoded'},
        )
        conn.getresponse()
        printlog(f'Sent Pushover [Put {collection} out tonight]')
    else:
        printlog(f'No collection tomorrow')


if __name__ == '__main__':    
    main()
    exit(0)