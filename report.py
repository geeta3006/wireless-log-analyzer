"""
HTML Report Generator
Takes analyzer results and produces a self-contained report.html
"""

import os
import json
import argparse
from analyzer import analyze


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wireless Log Analyzer Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: #0f1117; color: #e2e8f0; padding: 24px; }}
  h1 {{ font-size: 1.6rem; color: #63b3ed; margin-bottom: 4px; }}
  .subtitle {{ color: #718096; font-size: 0.85rem; margin-bottom: 24px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 28px; }}
  .card {{ background: #1a202c; border-radius: 10px; padding: 18px; border-left: 4px solid #63b3ed; }}
  .card.error {{ border-left-color: #fc8181; }}
  .card.warn  {{ border-left-color: #f6ad55; }}
  .card.ok    {{ border-left-color: #68d391; }}
  .card-label {{ font-size: 0.75rem; color: #718096; text-transform: uppercase; letter-spacing: 0.05em; }}
  .card-value {{ font-size: 2rem; font-weight: 700; margin-top: 4px; }}
  .card.error .card-value {{ color: #fc8181; }}
  .card.warn  .card-value {{ color: #f6ad55; }}
  .card.ok    .card-value {{ color: #68d391; }}
  section {{ background: #1a202c; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
  section h2 {{ font-size: 1rem; color: #a0aec0; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.05em; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
  th {{ text-align: left; color: #718096; font-weight: 500; padding: 6px 10px; border-bottom: 1px solid #2d3748; }}
  td {{ padding: 7px 10px; border-bottom: 1px solid #2d3748; }}
  tr:last-child td {{ border-bottom: none; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }}
  .badge-error {{ background: #742a2a; color: #fc8181; }}
  .badge-warn  {{ background: #7b341e; color: #f6ad55; }}
  .badge-info  {{ background: #1a365d; color: #63b3ed; }}
  .bar-wrap {{ background: #2d3748; border-radius: 4px; height: 8px; margin-top: 4px; }}
  .bar {{ background: #63b3ed; border-radius: 4px; height: 8px; }}
  .bar.red {{ background: #fc8181; }}
  .bar.yellow {{ background: #f6ad55; }}
  .log-table {{ font-size: 0.78rem; font-family: 'SF Mono', 'Fira Code', monospace; }}
  .log-table td {{ padding: 4px 8px; }}
</style>
</head>
<body>
<h1>📡 Wireless Log Analyzer</h1>
<p class="subtitle">Generated from {log_file} &nbsp;·&nbsp; {total} entries analyzed</p>

<div class="grid">
  <div class="card error">
    <div class="card-label">Failures</div>
    <div class="card-value">{errors}</div>
  </div>
  <div class="card warn">
    <div class="card-label">Warnings</div>
    <div class="card-value">{warnings}</div>
  </div>
  <div class="card ok">
    <div class="card-label">Normal</div>
    <div class="card-value">{info}</div>
  </div>
  <div class="card warn">
    <div class="card-label">Critical RSSI</div>
    <div class="card-value">{critical_rssi}</div>
  </div>
  <div class="card warn">
    <div class="card-label">High Latency</div>
    <div class="card-value">{high_latency}</div>
  </div>
  <div class="card error">
    <div class="card-label">Ping-Pong Streaks</div>
    <div class="card-value">{ping_pong}</div>
  </div>
</div>

<section>
  <h2>Average RF Metrics</h2>
  <table>
    <tr><th>Metric</th><th>Value</th><th></th></tr>
    <tr><td>RSSI</td><td>{avg_rssi} dBm</td>
        <td><div class="bar-wrap"><div class="bar red" style="width:{rssi_pct}%"></div></div></td></tr>
    <tr><td>SNR</td><td>{avg_snr} dB</td>
        <td><div class="bar-wrap"><div class="bar" style="width:{snr_pct}%"></div></div></td></tr>
    <tr><td>Throughput</td><td>{avg_tp} Mbps</td>
        <td><div class="bar-wrap"><div class="bar" style="width:{tp_pct}%"></div></div></td></tr>
    <tr><td>Latency</td><td>{avg_lat} ms</td>
        <td><div class="bar-wrap"><div class="bar yellow" style="width:{lat_pct}%"></div></div></td></tr>
  </table>
</section>

<section>
  <h2>Failures by Technology</h2>
  <table>
    <tr><th>Technology</th><th>Failure Type</th><th>Count</th></tr>
    {failures_by_tech_rows}
  </table>
</section>

<section>
  <h2>Top Failure Events</h2>
  <table>
    <tr><th>Event</th><th>Count</th><th></th></tr>
    {failure_event_rows}
  </table>
</section>

<section>
  <h2>Failures by Band</h2>
  <table>
    <tr><th>Technology / Band</th><th>Failures</th><th></th></tr>
    {band_rows}
  </table>
</section>

<section>
  <h2>Recent Error Log Entries (last 20)</h2>
  <table class="log-table">
    <tr><th>Timestamp</th><th>Level</th><th>Tech</th><th>Band</th><th>Event</th><th>RSSI</th><th>SNR</th></tr>
    {log_rows}
  </table>
</section>

</body>
</html>
"""


def badge(level):
    cls = {"ERROR": "badge-error", "WARN": "badge-warn", "INFO": "badge-info"}.get(level, "badge-info")
    return f'<span class="badge {cls}">{level}</span>'


def bar_row(label, count, max_count):
    pct = int((count / max_count) * 100) if max_count else 0
    return (f'<tr><td>{label}</td><td>{count}</td>'
            f'<td><div class="bar-wrap"><div class="bar" style="width:{pct}%"></div></div></td></tr>')


def generate_report(log_file: str = "synthetic_logs.jsonl", output_file: str = "report.html"):
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file)
    results = analyze(log_path)

    # Failures by tech rows
    fbt_rows = []
    for tech, failures in sorted(results["failures_by_tech"].items()):
        for event, count in sorted(failures.items(), key=lambda x: -x[1]):
            fbt_rows.append(f"<tr><td>{tech}</td><td>{event}</td><td>{count}</td></tr>")

    # Failure event rows
    skip = {"NORMAL_OPERATION", "HANDOFF_INITIATED", "SIGNAL_DEGRADATION", "PING_PONG_HANDOFF"}
    failure_events = {k: v for k, v in results["event_counts"].items() if k not in skip}
    max_fe = max(failure_events.values(), default=1)
    fe_rows = [bar_row(k, v, max_fe) for k, v in sorted(failure_events.items(), key=lambda x: -x[1])[:10]]

    # Band rows
    max_band = max(results["failures_by_band"].values(), default=1)
    band_rows = [bar_row(k, v, max_band)
                 for k, v in sorted(results["failures_by_band"].items(), key=lambda x: -x[1])[:10]]

    # Recent error log rows
    errors = [e for e in results["raw_logs"] if e.get("level") == "ERROR"][-20:]
    log_rows = []
    for e in reversed(errors):
        log_rows.append(
            f'<tr><td>{e["timestamp"]}</td><td>{badge(e["level"])}</td>'
            f'<td>{e.get("technology","")}</td><td>{e.get("band","")}</td>'
            f'<td>{e.get("event","")}</td>'
            f'<td>{e.get("rssi_dbm","")}</td><td>{e.get("snr_db","")}</td></tr>'
        )

    # Metric bar percentages (normalized for display)
    rssi_pct = min(100, int(abs(results["avg_rssi_dbm"] + 50) / 60 * 100))
    snr_pct  = min(100, int((results["avg_snr_db"] + 5) / 35 * 100))
    tp_pct   = min(100, int(results["avg_throughput_mbps"] / 150 * 100))
    lat_pct  = min(100, int(results["avg_latency_ms"] / 500 * 100))

    html = HTML_TEMPLATE.format(
        log_file=log_file,
        total=results["total_entries"],
        errors=results["level_counts"].get("ERROR", 0),
        warnings=results["level_counts"].get("WARN", 0),
        info=results["level_counts"].get("INFO", 0),
        critical_rssi=results["critical_rssi_count"],
        high_latency=results["high_latency_count"],
        ping_pong=results["ping_pong_streaks"],
        avg_rssi=results["avg_rssi_dbm"],
        avg_snr=results["avg_snr_db"],
        avg_tp=results["avg_throughput_mbps"],
        avg_lat=results["avg_latency_ms"],
        rssi_pct=rssi_pct, snr_pct=snr_pct, tp_pct=tp_pct, lat_pct=lat_pct,
        failures_by_tech_rows="\n    ".join(fbt_rows),
        failure_event_rows="\n    ".join(fe_rows),
        band_rows="\n    ".join(band_rows),
        log_rows="\n    ".join(log_rows),
    )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    with open(out_path, "w") as f:
        f.write(html)

    print(f"✓ Report saved → {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate HTML report from wireless logs")
    parser.add_argument("--input",  type=str, default="synthetic_logs.jsonl")
    parser.add_argument("--output", type=str, default="report.html")
    args = parser.parse_args()
    generate_report(log_file=args.input, output_file=args.output)
