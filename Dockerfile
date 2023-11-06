FROM python:3.10-alpine
RUN apk update && apk upgrade
RUN pip install -U pip poetry==1.1.13
WORKDIR /app
COPY . .
RUN poetry export --without-hashes --format=requirements.txt > requirements.txt
RUN pip install -r requirements.txt
EXPOSE 8000
ENTRYPOINT [ "python" ]
FROM python:3.10-alpine
RUN apk update && apk upgrade
RUN pip install -U pip poetry==1.1.13
WORKDIR /app
COPY . .
RUN poetry export --without-hashes --format=requirements.txt > requirements.txt
RUN pip install -r requirements.txt
EXPOSE 8000
ENTRYPOINT [ "python" ]
CMD ["-m uvicorn main:app --reload --port 8000"]
