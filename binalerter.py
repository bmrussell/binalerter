import datetime
from datetime import date, timedelta, datetime
import requests
import json
import confuse
from os.path import join, dirname
from time import strptime
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import urlencode
import http.client, urllib

def printlog(message):
    t = datetime.now().strftime(f'%d/%M/%Y %H:%M:%S')
    print(f'{t}\t{message}')

def get_collections(soup):
    # Extract the relevant tags
    days = soup.find_all("span", class_="card-collection-day")
    dates = soup.find_all("span", class_="card-collection-date")
    months = soup.find_all("span", class_="card-collection-month")

    collection_lis = soup.find_all("li", class_=["collection-type-RES", "collection-type-POD", "collection-type-CGW"])

    results = []

    # Check that all parts align
    if len(days) == len(dates) == len(months) == len(collection_lis):
        for day, date, month, li in zip(days, dates, months, collection_lis):
            # Build full date string
            day_str = day.get_text(strip=True)
            date_str = date.get_text(strip=True)
            month_str = month.get_text(strip=True)
            collection_str = li.get_text(strip=True)
            
            # Combine and parse into datetime object
            full_date_str = f"{day_str} {date_str} {month_str}"
            try:
                parsed_date = datetime.strptime(full_date_str, "%A %d %B %Y").date()
            except ValueError:
                # Fallback in case of formatting issues
                parsed_date = full_date_str

            results.append([parsed_date, collection_str])
    else:
        raise ValueError("Mismatched counts of date parts and collection types.")    
    
    return results
    
    
    
def main() -> None:
    # Get parameters
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
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

    if address_url is None or collection_url is None:
        printlog("URL is None!")
        exit()
        
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
    r = requests.post(address_url, data=params) # type: ignore
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
    r = requests.post(collection_url, data=params) # type: ignore
    soup = BeautifulSoup(r.text, 'html.parser')
    
    collections = get_collections(soup)
    printlog(f'Got {len(collections)} collection days')

    # See if the next collection is tomorrow
    tomorrow = date.today() + timedelta(days=1)
    collection = next((entry for entry in collections if entry[0] == tomorrow), None)
    
    # Send alert if the collection was found to be tomorrow
    if collection != None:
        printlog(f'Collection tomorrow')
        conn = http.client.HTTPSConnection('api.pushover.net:443')
        conn.request(
            'POST',
            '/1/messages.json',
            urlencode(
                {
                    'token': f'{pushoverToken}',
                    'user': f'{pushoverKey}',
                    'message': f'Put {collection[1]} out tonight',
                }
            ),
            {'Content-type': 'application/x-www-form-urlencoded'},
        )
        conn.getresponse()
        printlog(f'Sent Pushover [Put {collection[1]} out tonight]')
    else:
        printlog(f'No collection tomorrow')


if __name__ == '__main__':    
    main()
    exit(0)