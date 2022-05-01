# Start from standard python image
FROM python:3

WORKDIR /usr/src/BinAlerter

COPY requirements.txt .
# Python Confuse library override for location of config.yaml file
# See https://confuse.readthedocs.io/en/latest/usage.html#search-paths
ENV BINALERTERDIR=/usr/src/BinAlerter
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./
COPY ./config/config.yaml ./

CMD [ "python", "./main.py" ]
