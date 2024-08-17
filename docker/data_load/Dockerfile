FROM python:3.12-slim-bullseye


COPY src/data_preprocess/requirements.txt /requirements.txt

RUN python -m pip install -r requirements.txt

COPY src/__init__.py /src/__init__.py

COPY src/data_preprocess /src/data_preprocess

COPY .env /.env

ENV BASE_URL=http://212.56.152.36:8080
ENV DATA_PATH=src/data_preprocess/data
ENV PYTHONPATH="${PYTHONPATH}:/PigeonRacing"

ENTRYPOINT ["python", "/src/data_preprocess/data_load.py"]
