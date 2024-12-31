import json
import pendulum
from query.builder import (
    paginated_query_restaurants,
    batch_create_restaurants,
    delete_restaurant,
    update_restaurant,
    create_request_history,
)
import os
from query.common import (
    Restaurant,
    RequestHistory,
    RequestType,
    encrypt_data,
)
from query.clients import SESSION, SECRETS_MANAGER_CLIENT, KMS_CLIENT, LOGGER
from query.utils import (
    is_valid_create_restaurant,
    is_valid_update_restaurant,
    is_valid_delete_restaurant,
    record_to_create_restuarant,
    record_to_delete_restuarant,
)

service_kms_key_arn = os.getenv("SERVICE_KMS_KEY_ARN")
get_api_key_secret_response = SECRETS_MANAGER_CLIENT.get_secret_value(
    SecretId=os.getenv("API_KEY_SECRET_ID")
)
API_KEY = json.loads(get_api_key_secret_response["SecretString"])["apiKey"]


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
                {
                    "message": f"Something went wrong, requestId: {context.aws_request_id}"
                }
            ),
        }

    request = {
        "path": path,
        "http_method": http_method,
        "query_params": event.get("queryStringParameters"),
        "body": event.get("body"),
    }
    request_history = RequestHistory(
        request=encrypt_data(KMS_CLIENT, service_kms_key_arn, json.dumps(request)),
        response=encrypt_data(KMS_CLIENT, service_kms_key_arn, json.dumps(response)),
        request_type=request_type,
        request_time=request_time,
    )
    create_request_history(SESSION, request_history)
    return response


def authorize(event):
    header = event.get("headers", {})
    if not header or header is None or header == "null":
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

    next_page = int(query_params.get("nextPage", "1"))
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
        "body": json.dumps({"restaurantRecommendation": output, "nextPage": next_page}),
    }


def handleCreateRestaurant(event, context):
    if not authorize(event):
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Not Authorized"}),
        }

    body = json.loads(event.get("body", "{}"))
    restaurants = []
    for record in body.get("records", []):
        if not is_valid_create_restaurant(record):
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"message": "Object is not valid", "object": record}
                ),
            }
        restaurants.append(record_to_create_restuarant(record))
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

    body = json.loads(event.get("body", "{}"))
    record = body.get("record", {})
    if not is_valid_delete_restaurant(record):
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Object is not valid", "object": record}),
        }
    delete_restaurant(SESSION, record_to_delete_restuarant(record))
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

    body = json.loads(event.get("body", "{}"))
    record = body.get("record", {})
    if not is_valid_update_restaurant(record):
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Object is not valid", "object": record}),
        }

    update_restaurant(SESSION, record)
    LOGGER.info(f"Update restaurant completed successfully {record.get("name")}")
    return {
        "statusCode": 200,
        "body": json.dumps(
            {"message": f"Successfully updated {record.get("name")} restaurant"}
        ),
    }
