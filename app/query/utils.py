from query.common import Style, Restaurant, get_database_time


def is_valid_create_restaurant(record: dict):
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

    for key in required_keys:
        if key not in record:
            return False
    style = record["style"]
    if style.lower() not in Style._member_names_:
        return False
    return True


def record_to_create_restuarant(record: dict) -> Restaurant:
    timezone = record.get("timezone")
    open_hour = get_database_time(record.get("openHour"), timezone)
    close_hour = get_database_time(record.get("closeHour"), timezone)
    return Restaurant(
        name=record.get("name"),
        style=record.get("style").lower(),
        address=record.get("address"),
        open_hour=open_hour,
        close_hour=close_hour,
        vegetarian=str(record.get("vegetarian").lower()) == "true",
        delivers=str(record.get("delivers").lower()) == "true",
    )


def is_valid_delete_restaurant(record: dict):
    required_keys = ["name", "address"]
    for key in required_keys:
        if key not in record:
            return False
    return True


def record_to_delete_restuarant(record: dict) -> Restaurant:
    return Restaurant(name=record.get("name"), address=record.get("address"))


def is_valid_update_restaurant(record: dict):
    if len(record) <= 2:
        return False
    return is_valid_delete_restaurant(record)
