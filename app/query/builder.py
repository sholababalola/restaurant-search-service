from sqlalchemy import and_
from sqlalchemy.orm import declarative_base, Session, Query
from sqlalchemy.sql import ColumnExpressionArgument
import itertools
import os
import pendulum
import re
import pendulum
from query.common import (
    TimeContext,
    Restaurant,
    RequestHistory,
    Style,
    extract_time_and_context,
    get_database_time,
)
from sqlalchemy.sql import ColumnExpressionArgument

KEY_WORD_TO_COLUMN_MAP = dict(
    style=Restaurant.style,
    deliver=Restaurant.delivers,
    vegetarian=Restaurant.vegetarian,
    open_hour=Restaurant.open_hour,
    close_hour=Restaurant.close_hour,
)

MAX_CREATE_BATCH_SIZE = int(os.getenv("MAX_CREATE_BATCH_SIZE", "50"))
QUERY_PAGE_SIZE = int(os.getenv("QUERY_PAGE_SIZE", "20"))


def filter_negation_is_present(key_word: str, sentence: str):
    negation_prefixes = ["non-", "not "]
    for prefix in negation_prefixes:
        word_to_search = f"{prefix}{key_word}"
        if re.search(rf"\b{word_to_search}\b", sentence, re.IGNORECASE):
            return True
    return False


def filter_is_present(key_word: str, sentence: str):
    if re.search(rf"\b{key_word}\b", sentence, re.IGNORECASE):
        return True
    return False


def get_boolean_filter(key_word: str, sentence: str) -> ColumnExpressionArgument:
    # check negation first
    if filter_negation_is_present(key_word, sentence):
        return False
    elif filter_is_present(key_word, sentence):
        return True
    return False


def get_style_filter(sentence: str) -> ColumnExpressionArgument:
    filters = []
    for style in Style._member_names_:
        # check negation first
        if filter_negation_is_present(style, sentence):
            continue
        elif filter_is_present(style, sentence):
            filters.append(style)
    return filters


def add_style_filter(query: Query, filters: list[str]) -> Query:
    if len(filters) > 1:
        return query.filter(Restaurant.style.in_(filters))
    elif len(filters) == 1:
        return query.filter(Restaurant.style == filters[0])
    return query


def add_time_filter(
    query: Query, sentence: str, request_time: pendulum.DateTime
) -> Query:
    time_context = extract_time_and_context(sentence, request_time)
    if not time_context:
        return query

    hour = f"{time_context["time"]} {time_context["timezone"]}"
    if time_context["context"] == TimeContext.at:
        return query.filter(Restaurant.open_hour == hour)
    if time_context["context"] == TimeContext.by:
        return query.filter(Restaurant.open_hour <= hour).filter(
            Restaurant.close_hour > hour
        )
    if time_context["context"] == TimeContext.after:
        return query.filter(Restaurant.open_hour > hour)
    if time_context["context"] == TimeContext.before:
        return query.filter(Restaurant.open_hour < hour)


def paginated_query_restaurants(
    session: Session,
    sentence: str,
    request_time: pendulum.DateTime,
    page_number: int,
    page_size=QUERY_PAGE_SIZE,
):
    query = session.query(Restaurant).filter()
    query = add_style_filter(query, get_style_filter(sentence))

    for boolean_key_word in ["vegetarian", "deliver"]:
        filter = get_boolean_filter(boolean_key_word, sentence)
        if filter:
            query = query.filter(KEY_WORD_TO_COLUMN_MAP[boolean_key_word].is_(filter))

    query = add_time_filter(query, sentence, request_time)
    return query.offset((page_number - 1) * page_size).limit(page_size).all()


def batch_create_restaurants(
    session: Session,
    restaurants: list[Restaurant],
    create_batch_size=MAX_CREATE_BATCH_SIZE,
):
    for batch in list(itertools.batched(restaurants, create_batch_size)):
        session.add_all(batch)
        session.commit()


def delete_restaurant(
    session: Session,
    restaurant: Restaurant,
):
    db_restaurant = (
        session.query(Restaurant)
        .filter(Restaurant.name == restaurant.name)
        .filter(Restaurant.address == restaurant.address)
        .first()
    )
    if db_restaurant:
        session.delete(db_restaurant)
        session.commit()


def update_restaurant(
    session: Session,
    record: dict,
):
    db_restaurant = (
        session.query(Restaurant)
        .filter(Restaurant.name == record.get("name"))
        .filter(Restaurant.address == record.get("address"))
        .first()
    )
    if db_restaurant:
        if "style" in record:
            db_restaurant.style = record["style"].lower()
        if "openHour" in record and "timezone" in record:
            db_restaurant.open_hour = get_database_time(
                record["openHour"], record["timezone"]
            )
        if "closeHour" in record and "timezone" in record:
            db_restaurant.close_hour = get_database_time(
                record["closeHour"], record["timezone"]
            )
        if "vegetarian" in record:
            db_restaurant.vegetarian = record["vegetarian"].lower() == "true"

        if "delivers" in record:
            db_restaurant.delivers = record["delivers"].lower() == "true"

        session.commit()


def create_request_history(session: Session, request_history: RequestHistory):
    session.add(request_history)
    session.commit()
