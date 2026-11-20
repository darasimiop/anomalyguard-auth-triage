import pytest
from src.enrichment import enrich

@pytest.fixture
def sample_anomalies():
    """Provides a sample list of anomalies for testing."""
    return [
        {'timestamp': '2023-10-27T10:00:00Z', 'user': 'user1', 'ip': '192.0.2.1', 'event': 'failed_login'},
        {'timestamp': '2023-10-27T10:01:00Z', 'user': 'user2', 'ip': '203.0.113.5', 'event': 'sql_injection'},
        {'timestamp': '2023-10-27T10:02:00Z', 'user': 'user1', 'ip': '192.0.2.1', 'event': 'failed_login'},
        {'timestamp': '2023-10-27T10:03:00Z', 'user': 'user3', 'ip': '198.51.100.8', 'event': 'brute_force'},
        {'ip': '203.0.113.5', 'event': 'port_scan'}, # Missing timestamp and user
    ]

def test_enrich_geo_location(sample_anomalies):
    """Tests the geo-location enrichment logic."""
    enriched = enrich(sample_anomalies)
    assert enriched[0]['geo'] == 'US'
    assert enriched[1]['geo'] == 'EU'
    assert enriched[2]['geo'] == 'US'
    assert enriched[3]['geo'] == 'INTL'
    assert enriched[4]['geo'] == 'EU'

def test_enrich_timestamp_iso_format(sample_anomalies):
    """Tests the timestamp to ISO 8601 conversion."""
    enriched = enrich(sample_anomalies)
    # Check existing timestamps
    assert enriched[0]['timestamp_iso'] == '2023-10-27T10:00:00+00:00'
    # Missing event timestamps stay unknown.
    assert 'timestamp_iso' in enriched[4]
    assert enriched[4]['timestamp_iso'] is None

def test_enrich_occurrence_counting(sample_anomalies):
    """Tests the occurrence counting logic."""
    enriched = enrich(sample_anomalies)
    assert enriched[0]['occurrences'] == 2  # user1 appears twice
    assert enriched[1]['occurrences'] == 2  # ip 203.0.113.5 appears twice
    assert enriched[2]['occurrences'] == 2  # user1 appears twice
    assert enriched[3]['occurrences'] == 1  # user3 appears once
    assert enriched[4]['occurrences'] == 2  # ip 203.0.113.5 appears twice

def test_enrich_empty_list():
    """Tests that an empty list of anomalies is handled correctly."""
    assert enrich([]) == []

def test_enrich_preserves_original_keys(sample_anomalies):
    """Tests that original keys are preserved in the enriched data."""
    enriched = enrich(sample_anomalies)
    for original, result in zip(sample_anomalies, enriched):
        for key in original.keys():
            assert key in result
            assert original[key] == result[key]
