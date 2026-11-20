# src/detection.py

def detect_anomalies(data, threshold):
    """
    Detects anomalies in the data based on a simple rule.

    An event is considered an anomaly if its status is 'Failed' and its
    score exceeds the threshold.

    Args:
        data (list): A list of log entry dictionaries.
        threshold (float): The threshold for anomaly detection.

    Returns:
        list: A list of log entries that are considered anomalies.
    """
    anomalies = []
    print(f"    -> Analyzing {len(data)} log entries with threshold {threshold}...")
    for entry in data:
        # Coerce score to float safely
        try:
            score_val = float(entry.get('score', 0))
        except (TypeError, ValueError):
            score_val = 0.0

        is_anomaly = (
            entry.get("status") == "Failed" and
            score_val > threshold
        )
        if is_anomaly:
            anomalies.append(entry)
    
    print(f"    -> Found {len(anomalies)} anomalies.")
    return anomalies
