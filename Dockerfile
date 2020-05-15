FROM python:3.7-slim

COPY . .

RUN pip3 install -r requirements.txt

ENTRYPOINT python3 main.py
