# binalerter
Alerts which bins need to go out from North Wilts Waste collection calendar. Sends notifications via [Pushover](pushover.net/)

# Data Source

Scrapes https://ilforms.wiltshire.gov.uk/WasteCollectionDays/index

# Project Setup

## Virtual Environment
`virtualenv binEnv`

## Dependencies

See `requirements.txt`:

    .\binEnv\Scripts\python.exe -m pip install beautifulsoup4
    .\binEnv\Scripts\python.exe -m pip install pyyaml
    .\binEnv\Scripts\python.exe -m pip install requests
    .\binEnv\Scripts\python.exe -m pip install confuse
    .\binEnv\Scripts\python.exe -m pip install schedule    


# Running in Docker

1. Place `config.yaml` in `%APPDATA%\BinAlerter` 
2. Edit `config.yaml` to supply address, schedule to check, and PushOver API credentials
3. Run with Docker:

    ```docker container run -d --mount type=bind,source="%APPDATA%\BinAlerter",target=/usr/src/app/config binalerter```