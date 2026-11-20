"""Coordinate the original rule-based detection pipeline."""

import argparse
from time import perf_counter

from src.classifier import classify_anomalies
from src.detection import detect_anomalies
from src.enrichment import enrich
from src.ingest import ingest_data
from src.reporting import report_results


def analyze(records, threshold):
    """Process one independent batch and return its classified findings."""
    return classify_anomalies(enrich(detect_anomalies(records, threshold)))


def main():
    parser = argparse.ArgumentParser(description="Analyze authentication event JSONL.")
    parser.add_argument("--input", required=True, help="Path to the input JSONL.")
    parser.add_argument("--threshold", type=float, default=0.8, help="Exclusive score threshold from 0 to 1.")
    parser.add_argument("--output", default="report", help="Output path prefix, without an extension.")
    parser.add_argument("--profile", action="store_true", help="Print elapsed time for this run.")
    args = parser.parse_args()
    if not 0 <= args.threshold <= 1:
        parser.error("--threshold must be between 0 and 1.")
    start = perf_counter()
    try:
        records = ingest_data(args.input)
        findings = analyze(records, args.threshold)
        report_results(findings, args.output)
    except (ValueError, OSError, RecursionError) as error:
        parser.exit(2, f"AnomalyGuard could not complete the run: {error}\n")
    print(f"Processed {len(records)} events and reported {len(findings)} findings.")
    if args.profile:
        print(f"Elapsed time: {perf_counter() - start:.3f} seconds")


if __name__ == "__main__":
    main()
