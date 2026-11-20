from collections import Counter

def classify_anomalies(anomalies):
    """
    Classifies a list of anomalies based on a set of rules.

    Args:
        anomalies (list): A list of anomaly dictionaries.

    Returns:
        list: The list of anomalies with added 'class', 'reason', and 'severity' keys.
    """
    # Count user failures and IP occurrences for rule evaluation
    user_failure_counts = Counter()
    ip_counts = Counter()
    for anomaly in anomalies:
        # Heuristic for failure-like events
        if any(keyword in (anomaly.get('event') or '').lower() for keyword in ['fail', 'invalid', 'denied']):
            if 'user' in anomaly:
                user_failure_counts[anomaly['user']] += 1
        if 'ip' in anomaly:
            ip_counts[anomaly['ip']] += 1

    classified_anomalies = []
    for anomaly in anomalies:
        # Default classification
        classification = {
            'class': 'Other',
            'severity': 'low',
            'reason': 'no specific rule matched'
        }
        
        user = anomaly.get('user')
        ip = anomaly.get('ip')
        # Ensure score numeric for comparisons
        try:
            score = float(anomaly.get('score', 0))
        except (TypeError, ValueError):
            score = 0.0

        # Rule 1: FailedLoginSpike
        if user and user_failure_counts.get(user, 0) >= 3:
            classification['class'] = 'FailedLoginSpike'
            classification['severity'] = 'high'
            classification['reason'] = '>=3 failures for user'
        # Rule 2: RepeatedSourceIP
        elif ip and ip_counts.get(ip, 0) >= 3:
            classification['class'] = 'RepeatedSourceIP'
            classification['severity'] = 'medium'
            classification['reason'] = 'repeated source ip'
        # Rule 3: HighScoreOutlier
        elif score >= 0.9:
            classification['class'] = 'HighScoreOutlier'
            classification['severity'] = 'medium'
            classification['reason'] = '>=0.9 score'

        anomaly.update(classification)
        classified_anomalies.append(anomaly)

    return classified_anomalies
