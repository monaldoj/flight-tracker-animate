import os
import requests
import flask
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config

DATABRICKS_WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")

if not DATABRICKS_WAREHOUSE_ID:
    print("Warning: DATABRICKS_WAREHOUSE_ID not set. Cannot pull data.")

def get_databricks_token():
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

    if not DATABRICKS_TOKEN:
        print("DATABRICKS_TOKEN not set in environment variables, using on-behalf-of authentication.")
        DATABRICKS_TOKEN = flask.request.headers.get('X-Forwarded-Access-Token')
    return DATABRICKS_TOKEN

def get_databricks_server_hostname():
    DATABRICKS_SERVER_HOSTNAME = os.getenv("DATABRICKS_HOST")
    if not DATABRICKS_SERVER_HOSTNAME:
        print("DATABRICKS_SERVER_HOSTNAME not set in environment variables pulling from config.")
        cfg = Config()
        DATABRICKS_SERVER_HOSTNAME = cfg.host
    return DATABRICKS_SERVER_HOSTNAME

def get_databricks_sp_token():
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

    if not DATABRICKS_TOKEN:
        print("DATABRICKS_TOKEN not set in environment variables, using SP authentication.")
        host = get_databricks_server_hostname()
        DATABRICKS_HOST = "https://" + host
        CLIENT_ID = os.getenv("DATABRICKS_CLIENT_ID")
        CLIENT_SECRET = os.getenv("DATABRICKS_CLIENT_SECRET")

        # OAuth endpoint for Databricks on GCP
        TOKEN_URL = f"{DATABRICKS_HOST}/oidc/v1/token"

        # Request an access token
        token_response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "scope": "all-apis",
            },
            auth=(CLIENT_ID, CLIENT_SECRET),
        )

        token_response.raise_for_status()
        DATABRICKS_TOKEN = token_response.json()["access_token"]

        print("SP access token retrieved successfully")

    return DATABRICKS_TOKEN

def sqlQuery(query: str) -> pd.DataFrame:
    """Execute a SQL query and return the result as a pandas DataFrame."""
    # print("RUNNING QUERY:", query)
    DATABRICKS_SERVER_HOSTNAME = get_databricks_server_hostname()
    DATABRICKS_TOKEN = get_databricks_token()
    with sql.connect(
        http_path=f"/sql/1.0/warehouses/{DATABRICKS_WAREHOUSE_ID}",
        server_hostname=DATABRICKS_SERVER_HOSTNAME,
        access_token=DATABRICKS_TOKEN
    ) as connection:
        print("CONNECTION MADE")
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=columns)
        return df