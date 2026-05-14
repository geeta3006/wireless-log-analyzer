"""
Synthetic Wireless Log Generator
Generates realistic modem/baseband logs simulating:
- Normal operation
- Handoff events
- Link failures
- RRC connection drops
- Signal degradation
- Ping-pong handoffs
- Satellite Doppler drift
"""

import random
import datetime
import json
import os
import argparse

# ── Configuration ─────────────────────────────────────────────────────────────

TECHNOLOGIES = ["LTE", "5G_NR", "SATELLITE"]
BANDS = {
    "LTE":       ["B1", "B2", "B4", "B12", "B17", "B66"],
    "5G_NR":     ["n77", "n260", "n261", "n41"],
    "SATELLITE": ["S-BAND", "L-BAND"],
}
FAILURE_TYPES = [
    "RRC_CONNECTION_FAILURE",
    "HANDOFF_TIMEOUT",
    "LINK_BUDGET_EXCEEDED",
    "PING_PONG_HANDOFF",
    "NAS_ATTACH_REJECT",
    "SATELLITE_DOPPLER_DRIFT",
    "PHY_SYNC_LOSS",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def random_timestamp(start: datetime.datetime, delta_seconds: float) -> str:
    t = start + datetime.timedelta(seconds=delta_seconds)
    return t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def random_rssi() -> float:
    return round(random.uniform(-110, -50), 1)

def random_snr() -> float:
    return round(random.uniform(-5, 30), 1)

def random_throughput_mbps() -> float:
    return round(random.uniform(0.5, 150.0), 2)

def random_latency_ms() -> float:
    return round(random.uniform(10, 400), 1)

# ── Log Entry Builders ────────────────────────────────────────────────────────

def normal_entry(ts, tech):
    band = random.choice(BANDS[tech])
    return {
        "timestamp": ts, "level": "INFO", "layer": random.choice(["PHY", "MAC", "RRC", "NAS"]),
        "technology": tech, "band": band, "state": "CONNECTED",
        "rssi_dbm": random_rssi(), "snr_db": random_snr(),
        "throughput_mbps": random_throughput_mbps(), "latency_ms": random_latency_ms(),
        "event": "NORMAL_OPERATION", "message": f"Steady link on {tech} {band}",
    }

def handoff_entry(ts, tech_from, tech_to):
    return {
        "timestamp": ts, "level": "INFO", "layer": "RRC",
        "technology": tech_from, "band": random.choice(BANDS[tech_from]), "state": "HANDOFF",
        "rssi_dbm": round(random.uniform(-100, -80), 1), "snr_db": round(random.uniform(-2, 8), 1),
        "throughput_mbps": 0.0, "latency_ms": round(random.uniform(50, 200), 1),
        "event": "HANDOFF_INITIATED", "target_technology": tech_to,
        "target_band": random.choice(BANDS[tech_to]),
        "message": f"Handoff from {tech_from} to {tech_to}",
    }

def failure_entry(ts, tech, failure):
    return {
        "timestamp": ts, "level": "ERROR", "layer": random.choice(["PHY", "RRC", "NAS"]),
        "technology": tech, "band": random.choice(BANDS[tech]),
        "state": "SEARCHING" if "SYNC" in failure else "DETACHED",
        "rssi_dbm": round(random.uniform(-115, -100), 1), "snr_db": round(random.uniform(-10, 0), 1),
        "throughput_mbps": 0.0, "latency_ms": 9999.0,
        "event": failure, "message": f"FAILURE detected: {failure} on {tech}",
    }

def degradation_entry(ts, tech):
    band = random.choice(BANDS[tech])
    return {
        "timestamp": ts, "level": "WARN", "layer": "PHY",
        "technology": tech, "band": band, "state": "CONNECTED",
        "rssi_dbm": round(random.uniform(-108, -95), 1), "snr_db": round(random.uniform(0, 5), 1),
        "throughput_mbps": round(random.uniform(0.1, 5.0), 2), "latency_ms": round(random.uniform(200, 600), 1),
        "event": "SIGNAL_DEGRADATION",
        "message": f"Signal degrading on {tech} {band} — possible interference",
    }

def ping_pong_entry(ts, tech):
    return {
        "timestamp": ts, "level": "WARN", "layer": "RRC",
        "technology": tech, "band": random.choice(BANDS[tech]), "state": "HANDOFF",
        "rssi_dbm": round(random.uniform(-95, -85), 1), "snr_db": round(random.uniform(2, 8), 1),
        "throughput_mbps": round(random.uniform(0.5, 10.0), 2), "latency_ms": round(random.uniform(80, 300), 1),
        "event": "PING_PONG_HANDOFF",
        "message": "Rapid oscillating handoff detected — threshold tuning needed",
    }

# ── Main Generator ────────────────────────────────────────────────────────────

def generate_logs(num_entries: int = 500, output_file: str = "synthetic_logs.jsonl") -> str:
    start_time = datetime.datetime(2026, 5, 13, 8, 0, 0)
    logs = []
    t = 0.0

    for _ in range(num_entries):
        t += random.uniform(0.5, 3.0)
        ts = random_timestamp(start_time, t)
        tech = random.choice(TECHNOLOGIES)
        roll = random.random()

        if roll < 0.60:
            logs.append(normal_entry(ts, tech))
        elif roll < 0.72:
            logs.append(degradation_entry(ts, tech))
        elif roll < 0.82:
            other = [x for x in TECHNOLOGIES if x != tech]
            logs.append(handoff_entry(ts, tech, random.choice(other)))
        elif roll < 0.90:
            logs.append(ping_pong_entry(ts, tech))
        else:
            logs.append(failure_entry(ts, tech, random.choice(FAILURE_TYPES)))

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    with open(output_path, "w") as f:
        for entry in logs:
            f.write(json.dumps(entry) + "\n")

    print(f"✓ Generated {len(logs)} log entries → {output_path}")
    return output_path


def main_cli():
    parser = argparse.ArgumentParser(description="Generate synthetic wireless logs")
    parser.add_argument("--count", type=int, default=500, help="Number of log entries (default: 500)")
    parser.add_argument("--output", type=str, default="synthetic_logs.jsonl", help="Output filename")
    args = parser.parse_args()
    generate_logs(num_entries=args.count, output_file=args.output)


if __name__ == "__main__":
    main_cli()
