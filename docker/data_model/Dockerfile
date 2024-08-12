FROM python:3.12-slim-bullseye

COPY src/__init__.py /src/__init__.py

COPY src/data_preprocess/data /src/data_preprocess/data

COPY src/data_train/ /src/data_train

COPY src/data_train/requirements.txt /requirements.txt

# use better method to ingest env vars
COPY .env /.env

RUN python -m pip install -r requirements.txt

RUN apt-get update
RUN apt-get install libgomp1

ENV DATA_PATH=src/data_preprocess/data
ENV MODEL_PATH=src/data_train/pre-trained
ENV PARAMS_PATH=src/data_train/resources
ENV PYTHONPATH="${PYTHONPATH}:/PigeonRacing"
