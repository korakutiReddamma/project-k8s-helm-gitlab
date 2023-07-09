import mysql.connector
from flask import Flask, render_template
from prometheus_client import make_wsgi_app, Counter
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

REQUEST_COUNT = Counter('flask_app_request_count', 'Total number of requests')  

app = Flask(__name__)

# To accept requests from all origins
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS, HEAD, GET, POST'
    return response

# Read database credentials from ConfigMap
user = os.getenv('DB_USER', 'default-user')
host = os.getenv('DB_HOST', 'default-host')
database = os.getenv('DB_NAME', 'default-database')

# Read database password from Secret
password = os.getenv('DB_PASSWORD')

# Read table name from environment variable
table_name = os.getenv('DB_TABLE', 'default-table')

@app.route('/')
def index():
    cnx = mysql.connector.connect(user=user, password=password,
                                   host=host, database=database)
    cursor = cnx.cursor()
    query = f"SELECT * FROM {table_name}"
    cursor.execute(query)
    rows = cursor.fetchall()
    cnx.close()
    REQUEST_COUNT.inc()
    return render_template('table.html', rows=rows)


# Step : Create Prometheus WSGI Middleware
app_dispatch = DispatcherMiddleware(app, {
    '/metrics': make_wsgi_app()
})

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 80, app_dispatch)