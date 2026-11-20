"""Local JSON HTTP interface for the AnomalyGuard pipeline."""

import argparse

from flask import Flask, jsonify, request

from src.ingest import InvalidRecord, normalize_http_line, validate_record
from src.main import analyze

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
MAX_EVENTS = 1000
HTTP_THRESHOLD = 0.5


@app.after_request
def protect_response(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.errorhandler(413)
def too_large(_error):
    return jsonify(ok=False, error="Request exceeds the 1 MiB limit."), 413


@app.get("/health")
def health_check():
    return jsonify(status="ok")


@app.post("/ingest")
def ingest_data():
    if not request.is_json:
        return jsonify(ok=False, error="Use application/json."), 415
    try:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            raise InvalidRecord("Submit a JSON event object or an object with a lines array.")
        if "lines" in payload:
            lines = payload["lines"]
            if not isinstance(lines, list) or len(lines) > MAX_EVENTS:
                raise InvalidRecord(f"lines must be an array of at most {MAX_EVENTS} events.")
            records = [normalize_http_line(line) for line in lines]
        else:
            records = [validate_record(payload)]
    except (InvalidRecord, RecursionError) as error:
        message = str(error) if isinstance(error, InvalidRecord) else "JSON nesting is too deep."
        return jsonify(ok=False, error=message), 400
    return jsonify(ok=True, report={"anomalies": analyze(records, HTTP_THRESHOLD)})


def run_mcp_server(host="127.0.0.1", port=8765, debug=False):
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the local AnomalyGuard HTTP service.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--debug", action="store_true", help="Enable the local development debugger.")
    args = parser.parse_args()
    run_mcp_server(port=args.port, debug=args.debug)
