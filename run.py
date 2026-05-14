"""
One-command runner: generate → analyze → report
Usage: python run.py [--count 500]
"""

import argparse
import os
import sys

# ensure local imports work when run from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_logs import generate_logs
from analyzer import analyze, print_summary
from report import generate_report


def main():
    parser = argparse.ArgumentParser(description="Wireless Log Analyzer — full pipeline")
    parser.add_argument("--count",  type=int, default=500, help="Number of synthetic log entries")
    parser.add_argument("--logfile", type=str, default="synthetic_logs.jsonl")
    parser.add_argument("--report",  type=str, default="report.html")
    args = parser.parse_args()

    print("\n🔧 Step 1/3 — Generating synthetic logs...")
    generate_logs(num_entries=args.count, output_file=args.logfile)

    print("\n🔍 Step 2/3 — Analyzing logs...")
    results = analyze(os.path.join(os.path.dirname(os.path.abspath(__file__)), args.logfile))
    print_summary(results)

    print("\n📊 Step 3/3 — Generating HTML report...")
    generate_report(log_file=args.logfile, output_file=args.report)

    print("\n✅ Done! Open report.html in your browser to view the full report.")


if __name__ == "__main__":
    main()
