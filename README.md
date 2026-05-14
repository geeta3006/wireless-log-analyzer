# 📡 Wireless Log Analyzer

Automated anomaly detection and visualization for **LTE**, **5G NR**, and **Satellite** connectivity logs.

Built for wireless test engineers — runs locally, in Docker, or deploys to any cloud.

---

## Quick Start

### Option 1 — Docker (recommended, zero setup)

```bash
docker compose up
```

Open http://localhost:8501 in your browser. Done.

### Option 2 — Python (local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Option 3 — Install as a package

```bash
pip install -e .

# Generate synthetic logs
wla-generate --count 1000 --output my_logs.jsonl

# Analyze from CLI
wla-analyze --input my_logs.jsonl
```

---

## Features

| Feature | Description |
|---|---|
| Synthetic log generation | Realistic LTE / 5G NR / Satellite logs with failures, degradation, handoffs |
| Anomaly detection | Hard failures, critical RSSI, high latency, ping-pong handoffs, failure streaks |
| Interactive dashboard | Streamlit UI with live filters, charts, and log explorer |
| RF metrics trends | RSSI, SNR, throughput, latency over time with threshold lines |
| Handoff flow diagram | Sankey chart of technology transitions |
| Upload real logs | Drop in your own `.jsonl` log files |
| CLI tools | `wla-generate` and `wla-analyze` for pipeline/CI use |

---

## Project Structure

```
wireless-log-analyzer/
├── app.py                    # Streamlit dashboard
├── analyzer.py               # Anomaly detection engine
├── generate_logs.py          # Synthetic log generator
├── report.py                 # Static HTML report generator
├── run.py                    # CLI pipeline runner
├── setup.py                  # Python package definition
├── requirements.txt          # Pinned dependencies
├── Dockerfile                # Container image
├── docker-compose.yml        # One-command local deployment
├── .streamlit/
│   └── config.toml           # Streamlit theme + server config
├── data/                     # Mount point for real log files
└── .github/
    └── workflows/
        └── ci.yml            # GitHub Actions CI
```

---

## Log Format

Logs are newline-delimited JSON (`.jsonl`). Each entry:

```json
{
  "timestamp": "2026-05-13T08:00:01.234Z",
  "level": "ERROR",
  "layer": "RRC",
  "technology": "5G_NR",
  "band": "n77",
  "state": "DETACHED",
  "rssi_dbm": -108.3,
  "snr_db": -2.1,
  "throughput_mbps": 0.0,
  "latency_ms": 9999.0,
  "event": "RRC_CONNECTION_FAILURE",
  "message": "FAILURE detected: RRC_CONNECTION_FAILURE on 5G_NR"
}
```

To use real logs, convert them to this format and upload via the UI or mount into `./data/`.

---

## Technologies Covered

| Technology | Bands |
|---|---|
| LTE | B1, B2, B4, B12, B17, B66 |
| 5G NR | n41, n77, n260, n261 |
| Satellite | S-BAND, L-BAND |

---

## Deployment

### Deploy to Streamlit Cloud (free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set main file to `app.py`
4. Deploy — public URL in ~2 minutes

### Deploy to AWS / GCP / Azure

Use the provided `Dockerfile`. The container listens on port `8501`.

```bash
docker build -t wireless-log-analyzer .
docker run -p 8501:8501 wireless-log-analyzer
```

---

## Extending

- **Real log parsers** — replace `generate_logs.py` with parsers for QXDM, syslog, or custom formats
- **ML anomaly detection** — add scikit-learn models in `analyzer.py`
- **Alerting** — add Slack/email hooks when failure thresholds are crossed
- **Database backend** — swap the `.jsonl` file for a PostgreSQL or TimescaleDB store
- **CI regression tracking** — run `wla-analyze` in GitHub Actions and fail the build on error rate spikes
