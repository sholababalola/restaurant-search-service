import logging
import json
import pendulum
from query.builder import (
    paginated_query_restaurants,
    batch_create_restaurants,
    delete_restaurant,
    update_restaurant,
    create_request_history,
)
import boto3
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from query.common import (
    Base,
    Restaurant,
    RequestHistory,
    Style,
    RequestType,
    get_database_time,
)

client = boto3.client("secretsmanager")
get_database_secret_response = client.get_secret_value(
    SecretId=os.getenv("DATABASE_CREDENTIAL_SECRET_ID")
)
secret = json.loads(get_database_secret_response["SecretString"])
database_endpoint = os.getenv("DATABASE_ENDPOINT")
database_name = os.getenv("DATABASE_NAME")
connection_string = f"postgresql+psycopg2://{secret['username']}:{secret['password']}@{database_endpoint}/{database_name}?sslmode=require"
engine = create_engine(connection_string, echo=True)
Base.metadata.create_all(engine)
SESSION = Session(engine)

get_api_key_secret_response = client.get_secret_value(
    SecretId=os.getenv("API_KEY_SECRET_ID")
)
API_KEY = json.loads(get_api_key_secret_response["SecretString"])["apiKey"]

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

def lambda_handler(event, context):
    LOGGER.debug("Received event: {}".format(json.dumps(event)))
    request_time = pendulum.now(tz="UTC")
    path = event.get("path")
    http_method = event.get("httpMethod")
    response = None
    request_type = None
    try:
        if path == "/recommend" and http_method == "GET":
            LOGGER.info("handling get recommendation")
            request_type = RequestType.Recommend
            response = handleRecommendation(event, context)
        elif path == "/restaurant" and http_method == "POST":
            LOGGER.info("handling create restaurant")
            request_type = RequestType.Create
            response = handleCreateRestaurant(event, context)
        elif path == "/restaurant" and http_method == "PUT":
            LOGGER.info("handling update restaurant")
            request_type = RequestType.Update
            response = handleUpdateRestaurant(event, context)
        elif path == "/deleteRestaurant" and http_method == "POST":
            request_type = RequestType.Delete
            LOGGER.info("handling delete restaurant")
            response = handleDeleteRestaurant(event, context)
        else:
            LOGGER.info(f"Not implemented {path} {http_method}")
            response = {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
            request_type = RequestType.NotImplemented
    except Exception as e:
        LOGGER.error(e)
        response = {
            "statusCode": 500,
            "body": json.dumps(
                {"message": f"Something went wrong, requestId: {context.aws_request_id}"}
            ),
        }

    request = {
        "path": path,
        "http_method": http_method,
        "query_params": event.get("queryStringParameters"),
        "body": event.get("body"),
    }
    request_history = RequestHistory(
        request=request,
        response=response,
        request_type=request_type,
        request_time=request_time,
    )
    create_request_history(SESSION, request_history)
    return response


def authorize(event):
    header = event.get("headers", {})
    if not header or header is None or header == 'null':
        LOGGER.info(header)
        return False
    return API_KEY == header.get("X-AUTH-API-KEY")


def get_request_time(string_date_time):
    try:
        return pendulum.parse(string_date_time)
    except Exception as e:
        LOGGER.error(e)


def handleRecommendation(event, context):
    query_params = event.get("queryStringParameters") or {}
    if "query" not in query_params or "requestTime" not in query_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "query and requestTime required"}),
        }
    request_time = get_request_time(query_params.get("requestTime"))
    if not request_time:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "RequestTime is not properly formated"}),
        }

    next_page = int(query_params.get("next_page", "1"))
    output = []

    restaurant: Restaurant
    for restaurant in paginated_query_restaurants(
        SESSION, query_params.get("query"), request_time, next_page
    ):
        output.append(
            dict(
                name=restaurant.name,
                style=restaurant.style,
                address=restaurant.address,
                openHour=str(restaurant.open_hour),
                clouseHour=str(restaurant.close_hour),
                vegetarian=restaurant.vegetarian,
                delivers=restaurant.delivers,
            )
        )
    LOGGER.info("Get recommendation completed successfully")
    return {
        "statusCode": 200,
        "body": json.dumps({"restaurantRecommendation": output}),
    }


def handleCreateRestaurant(event, context):
    if not authorize(event):
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Not Authorized"}),
        }

    body = json.loads(event.get("body")) or {}
    restaurants = []
    required_keys = [
        "name",
        "style",
        "address",
        "openHour",
        "closeHour",
        "vegetarian",
        "delivers",
        "timezone",
    ]

    for record in body.get("records", []):
        for key in required_keys:
            if key not in record:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"message": f"Field {key} is required"}),
                }
        style = record["style"]
        if style.lower() not in Style._member_names_:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"message": f"style must be one of {str(Style._member_names_)}"}
                ),
            }
        timezone = record.get("timezone")
        open_hour = get_database_time(record.get("openHour"), timezone)
        close_hour = get_database_time(record.get("closeHour"), timezone)
        restaurants.append(
            Restaurant(
                name=record.get("name"),
                style=record.get("style").lower(),
                address=record.get("address"),
                open_hour=open_hour,
                close_hour=close_hour,
                vegetarian=record.get("vegetarian").lower() == "true",
                delivers=record.get("delivers").lower() == "true",
            )
        )
    batch_create_restaurants(SESSION, restaurants)
    LOGGER.info("Batch create completed successfully")
    return {
        "statusCode": 201,
        "body": json.dumps(
            {"message": f"Successfully created {len(restaurants)} records"}
        ),
    }


def handleDeleteRestaurant(event, context):
    if not authorize(event):
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Not Authorized"}),
        }

    body = json.loads(event.get("body")) or {}

    def validate_restaurant(record):
        required_keys = ["name", "address"]
        for key in required_keys:
            if key not in record:
                return {
                    "statusCode": 400,
                    "body": json.dumps({f"message": "Field {key} is required"}),
                }

    record = body.get("record", {})
    validate_restaurant(record)
    restaurant = Restaurant(name=record.get("name"), address=record.get("address"))
    delete_restaurant(SESSION, restaurant)
    LOGGER.info(f"Delete restaurant completed successfully {record.get("name")}")
    return {
        "statusCode": 200,
        "body": json.dumps(
            {"message": f"Successfully deleted {record.get("name")} restaurant"}
        ),
    }


def handleUpdateRestaurant(event, context):
    if not authorize(event):
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Not Authorized"}),
        }
    body = json.loads(event.get("body")) or {}

    def validate_restaurant(record):
        required_keys = ["name", "address"]
        for key in required_keys:
            if key not in record:
                return {
                    "statusCode": 400,
                    "body": json.dumps({f"message": "Field {key} is required"}),
                }

    record = body.get("record", {})
    validate_restaurant(record)
    update_restaurant(SESSION, record)
    LOGGER.info(f"Update restaurant completed successfully {record.get("name")}")
    return {
        "statusCode": 200,
        "body": json.dumps(
            {"message": f"Successfully updated {record.get("name")} restaurant"}
        ),
    }
