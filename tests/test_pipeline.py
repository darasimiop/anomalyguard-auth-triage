# tests/test_pipeline.py

import pytest
from src.detection import detect_anomalies
from src.ingest import ingest_data

def test_rule_only_anomaly_detection():
    """
    Tests that the basic rule (status == 'Failed') correctly identifies an anomaly,
    regardless of the score when the threshold is low.
    """
    sample_data = [
        {"status": "Success", "score": 0.9},
        {"status": "Failed", "score": 0.1}
    ]
    anomalies = detect_anomalies(sample_data, threshold=0.0)
    assert len(anomalies) == 1
    assert anomalies[0]["status"] == "Failed"

def test_threshold_behavior():
    """
    Tests the thresholding logic to ensure it correctly separates true positives
    from false positives.
    """
    sample_data = [
        {"status": "Failed", "score": 0.9},  # True positive
        {"status": "Failed", "score": 0.6}   # False positive (below threshold)
    ]
    anomalies = detect_anomalies(sample_data, threshold=0.7)
    assert len(anomalies) == 1
    assert anomalies[0]["score"] == 0.9

def test_missing_and_malformed_records():
    """
    Tests that the detection logic gracefully handles records that are missing
    the 'status' or 'score' keys.
    """
    sample_data = [
        {"status": "Failed"},              # Missing score
        {"score": 0.9},                    # Missing status
        {"status": "Success", "score": 0.95},
        {"status": "Failed", "score": 0.99} # Valid anomaly
    ]
    anomalies = detect_anomalies(sample_data, threshold=0.8)
    assert len(anomalies) == 1
    assert anomalies[0]["score"] == 0.99
