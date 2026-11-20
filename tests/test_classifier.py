import pytest
from src.classifier import classify_anomalies

def test_failed_login_spike():
    """Tests that 3+ failures for the same user trigger FailedLoginSpike."""
    anomalies = [
        {'user': 'testuser', 'event': 'login failed', 'score': 0.8},
        {'user': 'anotheruser', 'event': 'login ok', 'score': 0.1},
        {'user': 'testuser', 'event': 'invalid password', 'score': 0.8},
        {'user': 'testuser', 'event': 'access denied', 'score': 0.8},
    ]
    classified = classify_anomalies(anomalies)
    # Find the classified anomalies for 'testuser'
    testuser_anomalies = [a for a in classified if a['user'] == 'testuser']
    assert len(testuser_anomalies) == 3
    for anomaly in testuser_anomalies:
        assert anomaly['class'] == 'FailedLoginSpike'
        assert anomaly['severity'] == 'high'

def test_repeated_source_ip():
    """Tests that 3+ anomalies from the same IP trigger RepeatedSourceIP."""
    anomalies = [
        {'ip': '192.0.2.100', 'score': 0.7},
        {'ip': '198.51.100.5', 'score': 0.6},
        {'ip': '192.0.2.100', 'score': 0.7},
        {'ip': '192.0.2.100', 'score': 0.7},
    ]
    classified = classify_anomalies(anomalies)
    flagged_anomalies = [a for a in classified if a['ip'] == '192.0.2.100']
    assert len(flagged_anomalies) == 3
    # This rule applies to all anomalies from that IP
    for anomaly in flagged_anomalies:
        assert anomaly['class'] == 'RepeatedSourceIP'
        assert anomaly['severity'] == 'medium'

def test_high_score_outlier():
    """Tests that a score >= 0.9 triggers HighScoreOutlier."""
    anomalies = [
        {'user': 'test', 'score': 0.95},
        {'user': 'test2', 'score': 0.8},
    ]
    classified = classify_anomalies(anomalies)
    assert classified[0]['class'] == 'HighScoreOutlier'
    assert classified[0]['severity'] == 'medium'
    assert classified[1]['class'] == 'Other' # Ensure it doesn't misclassify

def test_other_case():
    """Tests the default 'Other' classification is applied correctly."""
    anomalies = [
        {'user': 'normaluser', 'event': 'login ok', 'score': 0.2},
        {'ip': '198.51.100.1', 'score': 0.5},
    ]
    classified = classify_anomalies(anomalies)
    assert all(a['class'] == 'Other' for a in classified)
    assert all(a['severity'] == 'low' for a in classified)
