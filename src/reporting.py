"""Write readable reports for one CLI run, including empty runs."""

import csv
from html import escape
import json
from pathlib import Path


FIELDS = (
    "timestamp_iso", "user", "ip", "event", "score", "class", "severity", "reason",
    "geo", "geo_source", "occurrences", "timestamp", "status",
)

HTML_START = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AnomalyGuard findings</title>
<style>
  body { margin: 0; background: #f2f6f5; color: #172e35; font: 16px system-ui, sans-serif; }
  main { max-width: 90rem; padding: 3rem 1.5rem; margin: auto; }
  h1 { color: #124b51; margin-bottom: .5rem; }
  p { margin: .65rem 0 1rem; }
  .table-wrap { overflow-x: auto; background: white; border: 1px solid #cad9d8; }
  table { width: 100%; border-collapse: collapse; font-size: .85rem; }
  th, td { padding: .65rem; border-bottom: 1px solid #dbe6e4; text-align: left; vertical-align: top; }
  th { background: #16464c; color: white; }
  tr:nth-child(even) { background: #f7faf9; }
</style>
</head>
<body><main>
<h1>AnomalyGuard findings</h1>
<p>Rule-based batch review. Severity reflects the matched rule. Geographic labels are simulated.</p>
"""


def spreadsheet_text(value):
    if isinstance(value, str) and value.startswith(("\t", "\r", "\n")):
        return "'" + value
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "＝", "＋", "－", "＠")):
        return "'" + value
    return value


def html_cell(value):
    return "Unknown" if value is None else escape(str(value))


def write_html(anomalies, fields, path):
    with path.open("w", encoding="utf-8", newline="\n") as out:
        out.write(HTML_START)
        out.write(f"<p><strong>{len(anomalies)}</strong> flagged records.</p>\n")
        if anomalies:
            out.write('<div class="table-wrap"><table><thead><tr>')
            for field in fields:
                label = "Geo (simulated)" if field == "geo" else field.replace("_", " ").capitalize()
                out.write(f'<th scope="col">{escape(label)}</th>')
            out.write("</tr></thead><tbody>\n")
            for finding in anomalies:
                cells = "".join(f"<td>{html_cell(finding.get(field))}</td>" for field in fields)
                out.write(f"<tr>{cells}</tr>\n")
            out.write("</tbody></table></div>\n")
        out.write("</main></body></html>\n")


def report_results(anomalies, base_filename="report"):
    """Write a JSON envelope, CSV table and HTML view for every completed run."""
    prefix = Path(base_filename)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    keys = set().union(*(row.keys() for row in anomalies))
    fields = [*FIELDS, *sorted(keys.difference(FIELDS))]

    path = Path(f"{prefix}.json")
    with path.open("w", encoding="utf-8", newline="\n") as out:
        json.dump({"anomalies": anomalies}, out, indent=2, allow_nan=False)
        out.write("\n")

    path = Path(f"{prefix}.csv")
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow([spreadsheet_text(field) for field in fields])
        for finding in anomalies:
            writer.writerow([spreadsheet_text(finding.get(field)) for field in fields])

    write_html(anomalies, fields, Path(f"{prefix}.html"))
