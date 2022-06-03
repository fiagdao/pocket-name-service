FROM python:latest

COPY ./requirements.txt .
RUN pip install -r requirements.txt

RUN git clone https://github.com/pokt-foundation/pypocket
RUN pip install wheel
RUN pip install -e ./pypocket

COPY ./ /indexer

WORKDIR /indexer

CMD [ "python", "./main.py"]
