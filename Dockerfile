FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt .
ENV BINALERTERDIR=./config
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .
COPY config.example.yaml ./config/

CMD [ "python", "./main.py" ]