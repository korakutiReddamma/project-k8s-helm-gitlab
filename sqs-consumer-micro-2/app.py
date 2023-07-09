from flask import Flask, jsonify
from prometheus_client import make_wsgi_app, Counter
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import threading
import boto3
import mysql.connector
import json
import os
from dotenv import load_dotenv

load_dotenv()

REQUEST_COUNT = Counter('flask_app_request_count', 'Total number of requests') 
app = Flask(__name__)

# AWS SQS configuration
region = os.environ.get('AWS_REGION')
queue_url = os.environ.get('QUEUE_URL')


def read_mysql_config():
    db_host = os.environ.get('DB_HOST')
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_name = os.environ.get('DB_NAME')
    db_table = os.environ.get('DB_TABLE')

    return db_host, db_user, db_password, db_name, db_table

# Create an SQS client
sqs = boto3.client('sqs', region_name=region)

# Create a MySQL connection
db_host, db_user, db_password, db_name, db_table = read_mysql_config()
mysql_conn = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name
)

# Create the MySQL table if it doesn't exist
cursor = mysql_conn.cursor()
create_table_query = f"CREATE TABLE IF NOT EXISTS {db_table} (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255), additional_data VARCHAR(255))"
cursor.execute(create_table_query)
mysql_conn.commit()
cursor.close()

# Function to process SQS messages and store in MySQL
def process_sqs_messages():
    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10
        )

        messages = response.get('Messages', [])

        for message in messages:
            body = message['Body']
            data = json.loads(body)

            name = data['name']
            email = data['email']
            additional_data = data['additionalData']

            cursor = mysql_conn.cursor()
            insert_query = f"INSERT INTO {db_table} (name, email, additional_data) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (name, email, additional_data))
            mysql_conn.commit()
            cursor.close()

            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )

# Start processing SQS messages in a separate thread
def start_message_processing():
    threading.Thread(target=process_sqs_messages).start()

@app.route('/')
def insert_data():
    start_message_processing()
    REQUEST_COUNT.inc()
    return jsonify({'message': 'Insert data successfully.'})

# Step 6: Create Prometheus WSGI Middleware
app_dispatch = DispatcherMiddleware(app, {
    '/metrics': make_wsgi_app()
})

# Step 7: Run the Flask Application
if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 5000, app_dispatch)
