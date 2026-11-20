import json
import os
import pytest
from src.main import main

@pytest.fixture
def setup_test_environment(tmp_path, monkeypatch):
    """
    Creates a temporary test environment with a sample input file.
    """
    sample_data = [
        {"timestamp": "2025-11-17T12:00:00Z", "event": "user alice logged in", "user": "alice", "ip": "192.0.2.1", "status": "Success", "score": 0.1},
        {"timestamp": "2025-11-17T12:01:00Z", "event": "user bob failed to log in", "user": "bob", "ip": "203.0.113.5", "status": "Failed", "score": 0.6},
        {"timestamp": "2025-11-17T12:02:00Z", "event": "user bob failed to log in", "user": "bob", "ip": "203.0.113.5", "status": "Failed", "score": 0.7},
        {"timestamp": "2025-11-17T12:03:00Z", "event": "user bob failed to log in", "user": "bob", "ip": "203.0.113.5", "status": "Failed", "score": 0.8},
        {"timestamp": "2025-11-17T12:04:00Z", "event": "user charlie accessed a critical file", "user": "charlie", "ip": "198.51.100.10", "status": "Success", "score": 0.2},
    ]
    
    input_file = tmp_path / "sample.jsonl"
    with open(input_file, "w") as f:
        for item in sample_data:
            f.write(json.dumps(item) + "\n")
            
    # Change the current working directory to the tmp_path
    monkeypatch.chdir(tmp_path)
    
    yield input_file

def test_pipeline_integration(setup_test_environment, monkeypatch):
    """
    Tests the full pipeline integration, from ingestion to reporting.
    """
    input_file = setup_test_environment
    
    # Mock command-line arguments
    monkeypatch.setattr("sys.argv", ["src/main.py", "--input", str(input_file), "--threshold", "0.5"])
    
    # Run the main pipeline
    main()
    
    # Assert that the reports are created
    assert os.path.exists("report.json")
    assert os.path.exists("report.csv")
    assert os.path.exists("report.html")
    
    # Assert the contents of the JSON report
    with open("report.json", "r") as f:
        report_data = json.load(f)
        
        assert "anomalies" in report_data
        assert len(report_data["anomalies"]) > 0
        
        for anomaly in report_data["anomalies"]:
            assert "timestamp_iso" in anomaly
            assert "geo" in anomaly
            assert "occurrences" in anomaly
            assert "class" in anomaly
            assert "severity" in anomaly
            assert "reason" in anomaly
