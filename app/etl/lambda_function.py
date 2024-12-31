import json
from query.builder import (
    batch_create_restaurants,
    delete_restaurant,
    update_restaurant,
)
from etl.utils import read_s3_file_by_lines, rows_to_object, S3StreamWriter
from query.clients import SESSION, LOGGER
from query.utils import (
    is_valid_create_restaurant,
    is_valid_update_restaurant,
    is_valid_delete_restaurant,
    record_to_create_restuarant,
    record_to_delete_restuarant,
)

DATA_SEPARATOR = "|"
S3_fILE_LIMIT = 1000000


def lambda_handler(event, context):
    LOGGER.debug("Received event: {}".format(json.dumps(event)))

    for record in event.get("Records", []):
        s3_info = record.get("s3", {})
        bucket_name = s3_info.get("bucket", {}).get("name")
        object_key: str = s3_info.get("object", {}).get("key")

        if object_key.startswith("create"):
            LOGGER.info("handling create restaurant")
            handleCreateRestaurant(bucket_name, object_key)
        elif object_key.startswith("update"):
            LOGGER.info("handling update restaurant")
            handleUpdateRestaurant(bucket_name, object_key)
        elif object_key.startswith("delete"):
            LOGGER.info("handling delete restaurant")
            handleDeleteRestaurant(bucket_name, object_key)
        else:
            LOGGER.warning(f"Not implemented {bucket_name} {object_key}")


def handleCreateRestaurant(bucket_name, object_key):
    count = 0
    s3_writer = S3StreamWriter(bucket_name, "unprocessed/create/", S3_fILE_LIMIT)
    headers = None
    restaurants = []
    try:
        for line in read_s3_file_by_lines(bucket_name, object_key):
            row = line.split(DATA_SEPARATOR)
            count += 1
            if count == 1:
                headers = row
                continue
            record = rows_to_object(headers, row)
            if not is_valid_create_restaurant(record):
                s3_writer.append(line.encode(encoding="utf-8"))
            restaurants.append(record_to_create_restuarant(record))

            if count >= 100:
                batch_create_restaurants(SESSION, restaurants)
                restaurants = []
    finally:
        s3_writer.close()


def handleDeleteRestaurant(bucket_name, object_key):
    count = 0
    s3_writer = S3StreamWriter(bucket_name, "unprocessed/delete/", S3_fILE_LIMIT)
    headers = None
    try:
        for line in read_s3_file_by_lines(bucket_name, object_key):
            row = line.split(DATA_SEPARATOR)
            count += 1
            if count == 1:
                headers = row
                continue
            record = rows_to_object(headers, row)
            if not is_valid_delete_restaurant(record):
                s3_writer.append(line.encode(encoding="utf-8"))
            delete_restaurant(SESSION, record_to_delete_restuarant(record))
    finally:
        s3_writer.close()


def handleUpdateRestaurant(bucket_name, object_key):
    count = 0
    s3_writer = S3StreamWriter(bucket_name, "unprocessed/update/", S3_fILE_LIMIT)
    headers = None
    try:
        for line in read_s3_file_by_lines(bucket_name, object_key):
            row = line.split(DATA_SEPARATOR)
            count += 1
            if count == 1:
                headers = row
                continue
            record = rows_to_object(headers, row)
            if not is_valid_update_restaurant(record):
                s3_writer.append(line.encode(encoding="utf-8"))
            update_restaurant(SESSION, record)
    finally:
        s3_writer.close()
