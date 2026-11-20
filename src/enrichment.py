"""Add batch-local context. Geographic labels are simulated."""

from collections import Counter
from datetime import datetime


def normalize_timestamp(value):
    if not value or not ("T" in value or " " in value):
        return None
    try:
        return datetime.fromisoformat(value).isoformat()
    except ValueError:
        return None


def enrich(anomalies):
    user_counts = Counter(row["user"] for row in anomalies if row.get("user"))
    ip_counts = Counter(row["ip"] for row in anomalies if row.get("ip"))
    result = []
    for anomaly in anomalies:
        event = anomaly.copy()
        ip = event.get("ip") or ""
        event["geo"] = "US" if ip.startswith("192.") else "EU" if ip.startswith("203.") else "INTL" if ip else None
        event["geo_source"] = "simulated_prefix"
        event["timestamp_iso"] = normalize_timestamp(event.get("timestamp"))
        event["occurrences"] = max(user_counts[event.get("user")], ip_counts[event.get("ip")])
        result.append(event)
    return result
