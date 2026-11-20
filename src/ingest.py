"""Read and validate event records at the CLI and HTTP boundaries."""

import json
import math
import re


class InvalidRecord(ValueError):
    """The submitted record cannot be safely analyzed."""


def validate_record(record):
    if not isinstance(record, dict):
        raise InvalidRecord("Each event must be a JSON object.")
    for key in ("timestamp", "event", "status", "user", "ip"):
        value = record.get(key)
        if value is not None and not isinstance(value, str):
            raise InvalidRecord(f"{key} must be a string or null.")
    value = record.get("score")
    if value is not None:
        try:
            score = float(value)
        except (ValueError, TypeError, OverflowError):
            raise InvalidRecord("score must be numeric and between 0 and 1.") from None
        if isinstance(value, bool) or not math.isfinite(score) or not 0 <= score <= 1:
            raise InvalidRecord("score must be numeric and between 0 and 1.")
    try:
        json.dumps(record, allow_nan=False)
    except (ValueError, TypeError, RecursionError):
        raise InvalidRecord("Event metadata must contain finite JSON values.") from None
    return record


def ingest_data(file_path):
    """Read JSONL, retaining unstructured lines as unscored events."""
    records = []
    with open(file_path, encoding="utf-8-sig") as source:
        for index, line in enumerate(source, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                record = {"event": line}
            try:
                if isinstance(record, dict) and isinstance(record.get("line"), str):
                    raw = record["line"]
                    try:
                        record = json.loads(raw)
                    except json.JSONDecodeError:
                        record = {"event": raw}
                records.append(validate_record(record))
            except InvalidRecord as error:
                raise InvalidRecord(f"Line {index}: {error}") from None
    return records


IP_TOKEN = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
USER_TOKEN = re.compile(r"\b(?:for\s+(?:(?:invalid\s+)?user\s+)?|user\s+)(\S+)", re.IGNORECASE)


def normalize_http_line(line):
    if isinstance(line, str):
        if line.lstrip().startswith("{"):
            try:
                record = json.loads(line)
            except (ValueError, RecursionError):
                raise InvalidRecord("A JSON event string is malformed.") from None
            return validate_record(record)
        failed = any(word in line.lower() for word in ("fail", "invalid", "denied"))
        match = USER_TOKEN.search(line)
        ip_match = IP_TOKEN.search(line)
        return {
            "event": line,
            "status": "Failed" if failed else "Other",
            "score": 0.9 if failed else 0.1,
            "user": match[1].rstrip(",") if match else None,
            "ip": ip_match[0] if ip_match else None,
        }
    return validate_record(line)
