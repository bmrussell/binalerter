# Binalerter
Alerts which bins need to go out from North Wilts Waste collection calendar. Sends notifications via [Pushover](pushover.net/)

# Data Source
Scrapes https://ilforms.wiltshire.gov.uk/WasteCollectionDays/index

# Prerequisites
[Pushover](https://pushover.net/) API key and token mobile app installed

# Project Setup

## Virtual Environment
```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

# Building
`build` script tags the image with `keep=true` so that it may be excluded with `podman prune`

```bash
podman image inspect binalerter --format '{{json .Config.Labels}}' | jq
{"keep":"true"}
```

# Running
```bash
python3 binalerter.py
```

# Running in Podman

1. Create `config.yaml` from the example
2. Build and name image
```bash
podman build --label=keep -t binalerter .
  ```
3. Run image

  ```bash
  podman run --name binalerter binalerter
  ```

4. Use the included quadlet files and deploy rootless with `./deploy.sh`

Make your user linger so user processes still hang around even if they're not logged in.
```bash
sudo loginctl enable-linger $USER
```

# Example config.yaml
```yaml
appName: BinAlerter

scrape:
  calendar_url: https://ilforms.wiltshire.gov.uk/WasteCollectionDays/index
  address_url: https://ilforms.wiltshire.gov.uk/WasteCollectionDays/AddressList
  collection_url: https://ilforms.wiltshire.gov.uk/WasteCollectionDays/CollectionList

location:
  postcode: XX9 6AR
  address: 42 Wallaby Way

pushover:
  apptoken: 012345678901234567890123456789
  userkey: 012345678901234567890123456789
```
