from sqlalchemy import (
    Column,
    String,
    Time,
    Boolean,
    BigInteger,
    Index,
    TIMESTAMP,
    Enum as SqlalchemyEnum,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

from enum import Enum
import re
from datetime import datetime
import pendulum
import logging

Base = declarative_base()

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


class TimeContext(Enum):
    at = 1
    by = 2
    after = 3
    before = 4


class RequestType(Enum):
    Recommend = 1
    Create = 2
    Update = 3
    Delete = 4
    NotImplemented = 5

class Style(Enum):
    italian = 1
    french  = 2 
    korean  = 3


class Restaurant(Base):
    __tablename__ = "restaurants"

    name = Column(String, primary_key=True, nullable=False)
    address = Column(String, primary_key=True, nullable=False)
    style = Column(String, nullable=False)
    open_hour = Column(Time(timezone=True), nullable=False)
    close_hour = Column(Time(timezone=True), nullable=False)
    vegetarian = Column(Boolean, nullable=False)
    delivers = Column(Boolean, nullable=False)

    __table_args__ = (
        Index("idx_style", "style"),
        Index("idx_style_vegetarian_delivers", "style", "vegetarian", "delivers"),
    )


class RequestHistory(Base):
    __tablename__ = "request_history"

    id = Column(BigInteger, primary_key=True)
    request = Column(JSONB, nullable=False)
    response = Column(JSONB, nullable=False)
    request_time = Column(TIMESTAMP(timezone=True), nullable=False)
    request_type = Column(SqlalchemyEnum(RequestType), nullable=False)

def get_database_time(time_str, timezone):
    return f"2000-01-01 {to_24_hour_format(time_str)} {timezone}"
    

def to_24_hour_format(time_str):
    """
    Convert time string to 24-hour format.
    """
    try:
        # Handle time with space (e.g., "8 AM")
        return datetime.strptime(time_str.strip(), "%I:%M %p").strftime("%H:%M")
    except ValueError:
        try:
            return datetime.strptime(time_str.strip(), "%I:%M%p").strftime("%H:%M")
        except ValueError:
            try:
                # Handle time without space (e.g., "8AM")
                return datetime.strptime(time_str.strip(), "%I%p").strftime("%H:%M")
            except ValueError:
                try:
                    return datetime.strptime(time_str.strip(), "%I %p").strftime(
                        "%H:%M"
                    )
                except ValueError:
                    try:
                        return datetime.strptime(time_str.strip(), "%H:%M").strftime(
                            "%H:%M"
                        )
                    except ValueError:
                        try:
                            return datetime.strptime(time_str.strip(), "%H").strftime(
                                "%H:%M"
                            )
                        except ValueError as e:
                            LOGGER.error(e)
                            raise e


def extract_time_and_context(sentence: str, request_time: pendulum.DateTime):
    """
    Times can be AM/PM or 24-hour format .
    Includes context words: at, by, after, before.
    Handles cases with or without spaces between time and AM/PM.
    """
    time_pattern = r"\b(at|by|after|before)?\b\s*(\d{1,2}(:\d{2})?(?:\s?[APap][Mm])?)"

    match = re.search(time_pattern, sentence, re.IGNORECASE)

    if match:
        context = match.group(1)  # Context word like 'at', 'by', etc.
        time = match.group(2)  # Single time in the match
        time_24_hours = to_24_hour_format(time)
        if time_24_hours:
            return {
                "context": TimeContext[context.lower()] if context else TimeContext.by,
                "time": time_24_hours,
                "timezone": request_time.timezone.name,
            }

    if "open now" in sentence or "open soon" in sentence:
        return {
            "context": TimeContext.by if "open now" in sentence else TimeContext.after,
            "time": request_time.strftime("%H:%M"),
            "timezone": request_time.timezone.name,
        }

    return None
