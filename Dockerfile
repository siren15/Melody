FROM python:3.10

COPY . /app/app

WORKDIR /app/app

RUN pip install -r requirements.txt

EXPOSE 443

CMD python -m uvicorn main:app --host 0.0.0.0 --port 443 --ssl-keyfile key.pem --ssl-certfile cert.pem

