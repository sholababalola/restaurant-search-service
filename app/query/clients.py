import logging
import json
import boto3
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from query.common import Base

SECRETS_MANAGER_CLIENT = boto3.client("secretsmanager")
get_database_secret_response = SECRETS_MANAGER_CLIENT.get_secret_value(
    SecretId=os.getenv("DATABASE_CREDENTIAL_SECRET_ID")
)
secret = json.loads(get_database_secret_response["SecretString"])
database_endpoint = os.getenv("DATABASE_ENDPOINT")
database_name = os.getenv("DATABASE_NAME")
connection_string = f"postgresql+psycopg2://{secret['username']}:{secret['password']}@{database_endpoint}/{database_name}?sslmode=require"
engine = create_engine(connection_string, echo=False)
Base.metadata.create_all(engine)

SESSION = Session(engine)

KMS_CLIENT = boto3.client("kms")

S3_CLIENT = boto3.client('s3')

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
