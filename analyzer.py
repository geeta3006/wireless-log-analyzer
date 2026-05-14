"""
Wireless Log Analyzer
Reads JSONL log files and detects:
- Hard failures (ERROR level)
- Signal degradation patterns
- Ping-pong handoffs
- Per-technology and per-band breakdowns
- Consecutive failure streaks
"""

import json
import os
import argparse
from collections import defaultdict, Counter
from typing import List, Dict, Any


# ── Thresholds ────────────────────────────────────────────────────────────────

RSSI_CRITICAL_DBM   = -105.0   # below this = critical signal
SNR_CRITICAL_DB     =   2.0    # below this = poor SNR
LATENCY_CRITICAL_MS = 500.0    # above this = unacceptable latency
PING_PONG_WINDOW    =   5      # consecutive handoffs to flag as ping-pong streak


# ── Loader ────────────────────────────────────────────────────────────────────

def load_logs(filepath: str) -> List[Dict[str, Any]]:
    logs = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                logs.append(json.loads(line))
    return logs


# ── Analysis Functions ────────────────────────────────────────────────────────

def count_by_level(logs):
    return Counter(e.get("level", "UNKNOWN") for e in logs)

def count_by_event(logs):
    return Counter(e.get("event", "UNKNOWN") for e in logs)

def count_by_technology(logs):
    return Counter(e.get("technology", "UNKNOWN") for e in logs)

def count_failures_by_tech(logs):
    result = defaultdict(Counter)
    for e in logs:
        if e.get("level") == "ERROR":
            result[e.get("technology", "UNKNOWN")][e.get("event", "UNKNOWN")] += 1
    return result

def count_by_band(logs):
    result = defaultdict(int)
    for e in logs:
        if e.get("level") == "ERROR":
            key = f"{e.get('technology','?')} {e.get('band','?')}"
            result[key] += 1
    return result

def detect_critical_rssi(logs):
    """Find entries where RSSI is critically low."""
    return [e for e in logs if e.get("rssi_dbm", 0) < RSSI_CRITICAL_DBM]

def detect_high_latency(logs):
    """Find entries with unacceptable latency (excluding known failure sentinel 9999)."""
    return [
        e for e in logs
        if LATENCY_CRITICAL_MS <= e.get("latency_ms", 0) < 9000
    ]

def detect_ping_pong_streaks(logs):
    """Find windows of consecutive ping-pong handoff events."""
    streaks = []
    streak = []
    for e in logs:
        if e.get("event") == "PING_PONG_HANDOFF":
            streak.append(e)
        else:
            if len(streak) >= PING_PONG_WINDOW:
                streaks.append(streak[:])
            streak = []
    if len(streak) >= PING_PONG_WINDOW:
        streaks.append(streak)
    return streaks

def detect_failure_streaks(logs, min_streak: int = 3):
    """Find runs of consecutive ERROR entries."""
    streaks = []
    streak = []
    for e in logs:
        if e.get("level") == "ERROR":
            streak.append(e)
        else:
            if len(streak) >= min_streak:
                streaks.append(streak[:])
            streak = []
    if len(streak) >= min_streak:
        streaks.append(streak)
    return streaks

def avg_metric(logs, key: str) -> float:
    vals = [e[key] for e in logs if key in e and e[key] < 9000]
    return round(sum(vals) / len(vals), 2) if vals else 0.0


# ── Report Builder ────────────────────────────────────────────────────────────

def analyze(filepath: str) -> Dict[str, Any]:
    logs = load_logs(filepath)
    total = len(logs)

    level_counts      = count_by_level(logs)
    event_counts      = count_by_event(logs)
    tech_counts       = count_by_technology(logs)
    failures_by_tech  = count_failures_by_tech(logs)
    failures_by_band  = count_by_band(logs)
    critical_rssi     = detect_critical_rssi(logs)
    high_latency      = detect_high_latency(logs)
    ping_pong_streaks = detect_ping_pong_streaks(logs)
    failure_streaks   = detect_failure_streaks(logs)

    results = {
        "total_entries":        total,
        "level_counts":         dict(level_counts),
        "event_counts":         dict(event_counts),
        "tech_counts":          dict(tech_counts),
        "failures_by_tech":     {k: dict(v) for k, v in failures_by_tech.items()},
        "failures_by_band":     dict(failures_by_band),
        "critical_rssi_count":  len(critical_rssi),
        "high_latency_count":   len(high_latency),
        "ping_pong_streaks":    len(ping_pong_streaks),
        "failure_streaks":      len(failure_streaks),
        "avg_rssi_dbm":         avg_metric(logs, "rssi_dbm"),
        "avg_snr_db":           avg_metric(logs, "snr_db"),
        "avg_throughput_mbps":  avg_metric(logs, "throughput_mbps"),
        "avg_latency_ms":       avg_metric(logs, "latency_ms"),
        "raw_logs":             logs,
    }
    return results


def print_summary(results: Dict[str, Any]):
    print("\n" + "=" * 55)
    print("  WIRELESS LOG ANALYZER — SUMMARY")
    print("=" * 55)
    print(f"  Total entries analyzed  : {results['total_entries']}")
    print(f"  Failures (ERROR)        : {results['level_counts'].get('ERROR', 0)}")
    print(f"  Warnings (WARN)         : {results['level_counts'].get('WARN', 0)}")
    print(f"  Normal (INFO)           : {results['level_counts'].get('INFO', 0)}")
    print()
    print(f"  Critical RSSI events    : {results['critical_rssi_count']}")
    print(f"  High latency events     : {results['high_latency_count']}")
    print(f"  Ping-pong streaks       : {results['ping_pong_streaks']}")
    print(f"  Failure streaks (≥3)    : {results['failure_streaks']}")
    print()
    print("  Avg RF Metrics (healthy entries):")
    print(f"    RSSI        : {results['avg_rssi_dbm']} dBm")
    print(f"    SNR         : {results['avg_snr_db']} dB")
    print(f"    Throughput  : {results['avg_throughput_mbps']} Mbps")
    print(f"    Latency     : {results['avg_latency_ms']} ms")
    print()
    print("  Events by technology:")
    for tech, count in sorted(results["tech_counts"].items()):
        print(f"    {tech:<12} : {count}")
    print()
    print("  Top failure types:")
    failure_events = {
        k: v for k, v in results["event_counts"].items()
        if k not in ("NORMAL_OPERATION", "HANDOFF_INITIATED", "SIGNAL_DEGRADATION", "PING_PONG_HANDOFF")
    }
    for event, count in sorted(failure_events.items(), key=lambda x: -x[1])[:8]:
        print(f"    {event:<35} : {count}")
    print()
    print("  Failures by band:")
    for band, count in sorted(results["failures_by_band"].items(), key=lambda x: -x[1])[:8]:
        print(f"    {band:<20} : {count}")
    print("=" * 55)


def main_cli():
    parser = argparse.ArgumentParser(description="Analyze wireless log file")
    parser.add_argument("--input", type=str, default="synthetic_logs.jsonl", help="Log file to analyze")
    args = parser.parse_args()

    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.input)
    if not os.path.exists(log_path):
        print(f"Log file not found: {log_path}")
        print("Run wla-generate first.")
        exit(1)

    results = analyze(log_path)
    print_summary(results)


if __name__ == "__main__":
    main_cli()
