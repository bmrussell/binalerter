# Start from standard python image
FROM python:3.13.9-slim

WORKDIR /app

COPY requirements.txt .

# Make Python Confuse library look for config.yaml file in the right place
# See https://confuse.readthedocs.io/en/latest/usage.html#search-paths
ENV BINALERTERDIR=/app

RUN pip install --no-cache-dir -r requirements.txt

COPY binalerter.py ./
COPY config.yaml ./

CMD [ "python3", "./binalerter.py" ]
