FROM python:3.11-alpine
RUN apk add --no-cache mariadb-connector-c mysql-client
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 80
ENTRYPOINT ["python"]
CMD ["/app/app.py"]