from query.clients import S3_CLIENT, LOGGER
import time
import json


def read_s3_file_by_lines(bucket_name, file_key):
    response = S3_CLIENT.get_object(Bucket=bucket_name, Key=file_key)
    body = response["Body"]
    for line in body.iter_lines():
        yield line.decode("utf-8")


def rows_to_object(headers: list[str], row: list[str]) -> dict:
    output = {}
    try:
        for index in range(len(headers)):
            output[headers[index]] = row[index]
    except Exception as e:
        LOGGER.error(f"Failed to convert row to record: {e}")
        LOGGER.error(f"row: {json.dumps(row)}")
        LOGGER.error(f"headers: {json.dumps(headers)}")

    return output


class S3StreamWriter:
    def __init__(self, bucket_name: str, key_prefix: str, max_size: int) -> None:
        """
        Args:
            bucket_name (str): The name of the S3 bucket.
            key_prefix (str): The key (path) in the S3 bucket to write the object.
            max_size (int): The maximum size (in bytes) before writing to S3.
        """
        self.bucket_name = bucket_name
        self.key_prefix = key_prefix
        self.max_size = max_size
        self.buffer = bytearray()
        self.part_number = 0

    def append(self, data: bytes) -> None:
        self.buffer.extend(data)
        if len(self.buffer) >= self.max_size:
            self._flush_to_s3()

    def _flush_to_s3(self) -> None:
        try:
            self.part_number += 1
            unique_key = f"{self.key_prefix}part_{self.part_number}_{int(time.time())}"
            LOGGER.info(f"Writing {len(self.buffer)} bytes to S3 as {unique_key}...")
            S3_CLIENT.put_object(
                Bucket=self.bucket_name, Key=unique_key, Body=self.buffer
            )
            self.buffer.clear()
        except Exception as e:
            LOGGER.error(f"Failed to write to S3: {e}")

    def close(self) -> None:
        if self.buffer and len(self.buffer) > 0:
            self._flush_to_s3()
