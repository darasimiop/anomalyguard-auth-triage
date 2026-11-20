import csv
import json

import pytest

from src.enrichment import enrich
from src.ingest import InvalidRecord, ingest_data
from src.main import analyze
from src.mcp_server import app, run_mcp_server
from src.reporting import report_results


@pytest.fixture
def client():
    return app.test_client()


def failure(user="example-alpha", score=0.95):
    return {"user": user, "ip": "203.0.113.42", "event": "failed authentication",
            "status": "Failed", "score": score}


def findings(response):
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    return response.get_json()["report"]["anomalies"]


def test_repeated_requests_stay_isolated(client, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    old_report = tmp_path / "report.json"
    old_report.write_text('{"anomalies":[{"user":"example-saved"}]}', encoding="utf-8")
    first = client.post("/ingest", json={"lines": [failure()] * 3})
    second = client.post("/ingest", json=failure("example-beta"))
    assert [row["class"] for row in findings(first)] == ["FailedLoginSpike"] * 3
    assert [(r["user"], r["class"], r["occurrences"]) for r in findings(second)] == [
        ("example-beta", "HighScoreOutlier", 1)
    ]
    assert findings(client.post("/ingest", json={"lines": []})) == []
    assert findings(client.post("/ingest", json={"status": "Success", "score": 0.95})) == []
    assert [p.name for p in tmp_path.iterdir()] == ["report.json"]
    assert json.loads(old_report.read_text())["anomalies"][0]["user"] == "example-saved"


@pytest.mark.parametrize("payload", [
    None, [], "example", {"lines": "example"}, {"lines": [42]},
    {"lines": ["{malformed JSON"]}, {"user": ["example"]}, {"score": "not numeric"},
    {"score": True}, {"score": "inf"}, {"score": 1.5},
    {"lines": [{}] * 1001},
])
def test_bad_json_shapes_return_400(client, payload):
    response = client.post("/ingest", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_http_status_and_request_limits(client):
    assert client.get("/health").get_json() == {"status": "ok"}
    assert client.post("/ingest", data="{}", content_type="text/plain").status_code == 415
    assert client.post("/ingest", data="{", content_type="application/json").status_code == 400
    assert client.post("/ingest", json={"lines": ["x" * (1024 * 1024)]}).status_code == 413



@pytest.mark.parametrize("event", [
    "authentication failed for example-alpha from 203.0.113.42",
    "invalid login for user example-alpha from 203.0.113.42",
    "Failed password for invalid user example-alpha from 203.0.113.42",
])
def test_http_plain_text_keeps_event_time_unknown(client, event):
    response = client.post("/ingest", json={"lines": [event]})
    row, = findings(response)
    assert row["user"] == "example-alpha"
    assert row["timestamp_iso"] is None
    assert row["geo_source"] == "simulated_prefix"


def test_timestamp_and_threshold_boundaries():
    assert enrich([{"timestamp": "bad date"}, {"timestamp": "2025-11-17"}])[0]["timestamp_iso"] is None
    assert enrich([{"timestamp": "2025-11-17"}])[0]["timestamp_iso"] is None
    assert analyze([failure(score=0.7)], 0.7) == []
    assert len(analyze([failure(score="0.71")], 0.7)) == 1


def test_cli_reports_invalid_records_with_line_number(tmp_path):
    file = tmp_path / "input.jsonl"
    file.write_text("{}\n42\n", encoding="utf-8")
    with pytest.raises(InvalidRecord, match="Line 2:"):
        ingest_data(file)


def test_reports_escape_and_clear_previous_results(tmp_path):
    base = tmp_path / "report"
    report_results([{"event": "review <example> & context", "user": "+ example-note", "+ note": "value"}], base)
    html = base.with_suffix(".html").read_text(encoding="utf-8")
    assert "review &lt;example&gt; &amp; context" in html
    with base.with_suffix(".csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["user"] == "'+ example-note"
    assert rows[0]["'+ note"] == "value"
    report_results([], base)
    assert json.loads(base.with_suffix(".json").read_text(encoding="utf-8")) == {"anomalies": []}
    assert "<strong>0</strong> flagged records" in base.with_suffix(".html").read_text(encoding="utf-8")
    with base.with_suffix(".csv").open(encoding="utf-8", newline="") as file:
        assert list(csv.DictReader(file)) == []


def test_server_defaults_to_local_without_debug(monkeypatch):
    options = {}
    monkeypatch.setattr(app, "run", lambda **kwargs: options.update(kwargs))
    run_mcp_server()
    assert options == {"host": "127.0.0.1", "port": 8765, "debug": False}
