"""
Wireless Log Analyzer — Streamlit Demo
Run with: streamlit run app.py
"""

import sys
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from collections import Counter

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_logs import generate_logs
from analyzer import analyze

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wireless Log Analyzer",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme colors ──────────────────────────────────────────────────────────────
COLOR_ERROR  = "#fc8181"
COLOR_WARN   = "#f6ad55"
COLOR_OK     = "#68d391"
COLOR_INFO   = "#63b3ed"
COLOR_BG     = "#1a202c"

TECH_COLORS = {
    "LTE":       "#63b3ed",
    "5G_NR":     "#68d391",
    "SATELLITE": "#f6ad55",
}

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 2rem !important; }
[data-testid="stMetricLabel"] { font-size: 0.8rem !important; color: #718096; }
.stMetric { background: #1a202c; border-radius: 10px; padding: 12px 16px; }
div[data-testid="metric-container"] {
    background: #1a202c;
    border-radius: 10px;
    padding: 14px 18px;
    border-left: 4px solid #63b3ed;
}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/antenna.png", width=60)
    st.title("📡 Wireless Log Analyzer")
    st.caption("Cellular & Satellite Test Automation")
    st.divider()

    st.subheader("Data Source")
    data_source = st.radio(
        "Choose input",
        ["Generate synthetic logs", "Upload a log file"],
        index=0,
    )

    uploaded_file = None
    log_count = 500

    if data_source == "Generate synthetic logs":
        log_count = st.slider("Number of log entries", 100, 2000, 500, step=100)
        seed = st.number_input("Random seed (0 = random)", min_value=0, max_value=9999, value=0)
        generate_btn = st.button("⚡ Generate & Analyze", type="primary", use_container_width=True)
    else:
        uploaded_file = st.file_uploader("Upload .jsonl log file", type=["jsonl", "json"])
        generate_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)

    st.divider()
    st.subheader("Filters")
    tech_filter = st.multiselect(
        "Technology",
        ["LTE", "5G_NR", "SATELLITE"],
        default=["LTE", "5G_NR", "SATELLITE"],
    )
    level_filter = st.multiselect(
        "Log Level",
        ["INFO", "WARN", "ERROR"],
        default=["INFO", "WARN", "ERROR"],
    )

    st.divider()
    st.caption("Built for wireless test automation · Apple-style RF testing")


# ── Session state ─────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = None
if "df" not in st.session_state:
    st.session_state.df = None


# ── Load / generate data ──────────────────────────────────────────────────────
def load_results_from_file(path):
    results = analyze(path)
    df = pd.DataFrame(results["raw_logs"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["latency_ms"] = df["latency_ms"].apply(lambda x: None if x >= 9000 else x)
    return results, df

if generate_btn:
    with st.spinner("Running analysis..."):
        if data_source == "Generate synthetic logs":
            import random
            if seed > 0:
                random.seed(seed)
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthetic_logs.jsonl")
            generate_logs(num_entries=log_count, output_file="synthetic_logs.jsonl")
            results, df = load_results_from_file(log_path)
        else:
            if uploaded_file:
                tmp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_uploaded.jsonl")
                with open(tmp_path, "wb") as f:
                    f.write(uploaded_file.read())
                results, df = load_results_from_file(tmp_path)
            else:
                st.warning("Please upload a log file first.")
                st.stop()

        st.session_state.results = results
        st.session_state.df = df

# ── Landing state ─────────────────────────────────────────────────────────────
if st.session_state.results is None:
    st.markdown("## 📡 Wireless Log Analyzer")
    st.markdown(
        "Automated anomaly detection for **LTE**, **5G NR**, and **Satellite** connectivity stacks.\n\n"
        "Use the sidebar to generate synthetic logs or upload your own `.jsonl` file, then click **Generate & Analyze**."
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Detects**\n- Hard failures (ERROR)\n- Signal degradation\n- Ping-pong handoffs\n- Failure streaks")
    with col2:
        st.info("**Covers**\n- LTE (B1–B66)\n- 5G NR (n41, n77, n260, n261)\n- Satellite (S-BAND, L-BAND)")
    with col3:
        st.info("**Metrics**\n- RSSI / SNR trends\n- Throughput over time\n- Latency distribution\n- Per-band breakdown")
    st.stop()

# ── Apply filters ─────────────────────────────────────────────────────────────
results = st.session_state.results
df_full = st.session_state.df.copy()

df = df_full[
    df_full["technology"].isin(tech_filter) &
    df_full["level"].isin(level_filter)
].copy()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 📡 Wireless Log Analyzer — Dashboard")
st.caption(f"Showing {len(df):,} of {len(df_full):,} entries after filters")

# ── KPI Row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)

errors  = len(df[df["level"] == "ERROR"])
warns   = len(df[df["level"] == "WARN"])
infos   = len(df[df["level"] == "INFO"])
crit_rssi = len(df[df["rssi_dbm"] < -105])
high_lat  = len(df[(df["latency_ms"].notna()) & (df["latency_ms"] > 500)])
pp_count  = len(df[df["event"] == "PING_PONG_HANDOFF"])

k1.metric("Total Entries",    f"{len(df):,}")
k2.metric("🔴 Failures",      f"{errors:,}",    delta=f"{errors/len(df)*100:.1f}%", delta_color="inverse")
k3.metric("🟡 Warnings",      f"{warns:,}")
k4.metric("Critical RSSI",    f"{crit_rssi:,}", delta_color="inverse")
k5.metric("High Latency",     f"{high_lat:,}",  delta_color="inverse")
k6.metric("Ping-Pong Events", f"{pp_count:,}",  delta_color="inverse")

st.divider()

# ── Row 1: Event timeline + Level donut ───────────────────────────────────────
col_left, col_right = st.columns([3, 1])

with col_left:
    st.subheader("Event Timeline")
    df_time = df.copy()
    df_time["minute"] = df_time["timestamp"].dt.floor("1min")
    timeline = df_time.groupby(["minute", "level"]).size().reset_index(name="count")
    level_color_map = {"INFO": COLOR_INFO, "WARN": COLOR_WARN, "ERROR": COLOR_ERROR}
    fig_timeline = px.bar(
        timeline, x="minute", y="count", color="level",
        color_discrete_map=level_color_map,
        labels={"minute": "Time", "count": "Events", "level": "Level"},
        template="plotly_dark",
    )
    fig_timeline.update_layout(
        plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=0, r=0, t=10, b=0), height=280,
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

with col_right:
    st.subheader("Log Levels")
    level_counts = df["level"].value_counts()
    fig_donut = go.Figure(go.Pie(
        labels=level_counts.index,
        values=level_counts.values,
        hole=0.55,
        marker_colors=[level_color_map.get(l, "#aaa") for l in level_counts.index],
        textinfo="label+percent",
    ))
    fig_donut.update_layout(
        template="plotly_dark", paper_bgcolor="#0f1117",
        showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=280,
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# ── Row 2: RF Metrics over time ───────────────────────────────────────────────
st.subheader("RF Metrics Over Time")
tab_rssi, tab_snr, tab_tp, tab_lat = st.tabs(["RSSI (dBm)", "SNR (dB)", "Throughput (Mbps)", "Latency (ms)"])

def rf_line_chart(col, title, color, threshold=None, threshold_label=None):
    df_rf = df[df[col].notna()].copy()
    df_rf = df_rf.sort_values("timestamp")
    fig = px.scatter(
        df_rf, x="timestamp", y=col, color="technology",
        color_discrete_map=TECH_COLORS,
        opacity=0.6, template="plotly_dark",
        labels={"timestamp": "Time", col: title},
    )
    if threshold is not None:
        fig.add_hline(
            y=threshold, line_dash="dash", line_color=COLOR_ERROR,
            annotation_text=threshold_label, annotation_position="top left",
        )
    fig.update_layout(
        plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
        margin=dict(l=0, r=0, t=10, b=0), height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig

with tab_rssi:
    st.plotly_chart(rf_line_chart("rssi_dbm", "RSSI (dBm)", COLOR_ERROR,
                                  threshold=-105, threshold_label="Critical threshold"),
                    use_container_width=True)

with tab_snr:
    st.plotly_chart(rf_line_chart("snr_db", "SNR (dB)", COLOR_INFO,
                                  threshold=2, threshold_label="Poor SNR"),
                    use_container_width=True)

with tab_tp:
    df_tp = df[df["throughput_mbps"] > 0].copy()
    fig_tp = px.line(
        df_tp.sort_values("timestamp"), x="timestamp", y="throughput_mbps",
        color="technology", color_discrete_map=TECH_COLORS,
        template="plotly_dark",
        labels={"timestamp": "Time", "throughput_mbps": "Throughput (Mbps)"},
    )
    fig_tp.update_layout(
        plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
        margin=dict(l=0, r=0, t=10, b=0), height=300,
    )
    st.plotly_chart(fig_tp, use_container_width=True)

with tab_lat:
    df_lat = df[df["latency_ms"].notna()].copy()
    fig_lat = px.histogram(
        df_lat, x="latency_ms", color="technology",
        color_discrete_map=TECH_COLORS, nbins=40,
        template="plotly_dark", opacity=0.8,
        labels={"latency_ms": "Latency (ms)", "count": "Events"},
    )
    fig_lat.add_vline(x=500, line_dash="dash", line_color=COLOR_ERROR,
                      annotation_text="500ms threshold")
    fig_lat.update_layout(
        plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
        margin=dict(l=0, r=0, t=10, b=0), height=300,
        barmode="overlay",
    )
    st.plotly_chart(fig_lat, use_container_width=True)

# ── Row 3: Failures breakdown ─────────────────────────────────────────────────
st.subheader("Failure Analysis")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("**Failures by Technology**")
    df_err = df[df["level"] == "ERROR"]
    tech_fail = df_err["technology"].value_counts().reset_index()
    tech_fail.columns = ["technology", "count"]
    fig_tech = px.bar(
        tech_fail, x="count", y="technology", orientation="h",
        color="technology", color_discrete_map=TECH_COLORS,
        template="plotly_dark",
    )
    fig_tech.update_layout(
        plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
        showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=260,
        yaxis_title="", xaxis_title="Failures",
    )
    st.plotly_chart(fig_tech, use_container_width=True)

with col_b:
    st.markdown("**Top Failure Types**")
    skip_events = {"NORMAL_OPERATION", "HANDOFF_INITIATED", "SIGNAL_DEGRADATION", "PING_PONG_HANDOFF"}
    df_fail_types = df[~df["event"].isin(skip_events) & (df["level"] == "ERROR")]
    fail_counts = df_fail_types["event"].value_counts().head(7).reset_index()
    fail_counts.columns = ["event", "count"]
    fig_fail = px.bar(
        fail_counts, x="count", y="event", orientation="h",
        color_discrete_sequence=[COLOR_ERROR],
        template="plotly_dark",
    )
    fig_fail.update_layout(
        plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
        showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=260,
        yaxis_title="", xaxis_title="Count",
    )
    st.plotly_chart(fig_fail, use_container_width=True)

with col_c:
    st.markdown("**Failures by Band**")
    df_err2 = df[df["level"] == "ERROR"].copy()
    df_err2["tech_band"] = df_err2["technology"] + " " + df_err2["band"]
    band_counts = df_err2["tech_band"].value_counts().head(8).reset_index()
    band_counts.columns = ["band", "count"]
    fig_band = px.bar(
        band_counts, x="count", y="band", orientation="h",
        color_discrete_sequence=[COLOR_WARN],
        template="plotly_dark",
    )
    fig_band.update_layout(
        plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
        showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=260,
        yaxis_title="", xaxis_title="Failures",
    )
    st.plotly_chart(fig_band, use_container_width=True)

# ── Row 4: Avg metrics cards ──────────────────────────────────────────────────
st.subheader("Average RF Metrics (filtered)")
m1, m2, m3, m4 = st.columns(4)

df_healthy = df[df["latency_ms"].notna()]
avg_rssi = round(df_healthy["rssi_dbm"].mean(), 1) if len(df_healthy) else 0
avg_snr  = round(df_healthy["snr_db"].mean(), 1)   if len(df_healthy) else 0
avg_tp   = round(df[df["throughput_mbps"] > 0]["throughput_mbps"].mean(), 1) if len(df) else 0
avg_lat  = round(df_healthy["latency_ms"].mean(), 1) if len(df_healthy) else 0

m1.metric("Avg RSSI",       f"{avg_rssi} dBm",  help="Target: > -95 dBm")
m2.metric("Avg SNR",        f"{avg_snr} dB",    help="Target: > 10 dB")
m3.metric("Avg Throughput", f"{avg_tp} Mbps",   help="Higher is better")
m4.metric("Avg Latency",    f"{avg_lat} ms",    help="Target: < 200 ms")

# ── Row 5: Handoff flow ───────────────────────────────────────────────────────
st.subheader("Handoff Flow (Technology Transitions)")
df_ho = df[df["event"] == "HANDOFF_INITIATED"].copy()
if "target_technology" in df_ho.columns and len(df_ho) > 0:
    df_ho = df_ho.dropna(subset=["target_technology"])
    sankey_data = df_ho.groupby(["technology", "target_technology"]).size().reset_index(name="count")
    all_nodes = list(set(sankey_data["technology"].tolist() + sankey_data["target_technology"].tolist()))
    node_idx = {n: i for i, n in enumerate(all_nodes)}
    node_colors = [TECH_COLORS.get(n, "#aaa") for n in all_nodes]

    fig_sankey = go.Figure(go.Sankey(
        node=dict(
            pad=20, thickness=20,
            label=all_nodes,
            color=node_colors,
        ),
        link=dict(
            source=[node_idx[r["technology"]] for _, r in sankey_data.iterrows()],
            target=[node_idx[r["target_technology"]] for _, r in sankey_data.iterrows()],
            value=sankey_data["count"].tolist(),
            color="rgba(99,179,237,0.3)",
        ),
    ))
    fig_sankey.update_layout(
        template="plotly_dark", paper_bgcolor="#0f1117",
        margin=dict(l=0, r=0, t=10, b=0), height=300,
    )
    st.plotly_chart(fig_sankey, use_container_width=True)
else:
    st.info("No handoff events in current filter selection.")

# ── Row 6: Raw log table ──────────────────────────────────────────────────────
st.subheader("Log Explorer")

col_search, col_event_filter, col_layer_filter = st.columns([2, 2, 2])
with col_search:
    search_text = st.text_input("Search messages", placeholder="e.g. FAILURE, RRC, n260")
with col_event_filter:
    all_events = sorted(df["event"].unique().tolist())
    event_sel = st.multiselect("Filter by event", all_events, default=[])
with col_layer_filter:
    all_layers = sorted(df["layer"].dropna().unique().tolist()) if "layer" in df.columns else []
    layer_sel = st.multiselect("Filter by layer", all_layers, default=[])

df_table = df.copy()
if search_text:
    df_table = df_table[df_table["message"].str.contains(search_text, case=False, na=False)]
if event_sel:
    df_table = df_table[df_table["event"].isin(event_sel)]
if layer_sel:
    df_table = df_table[df_table["layer"].isin(layer_sel)]

display_cols = ["timestamp", "level", "technology", "band", "layer", "state",
                "rssi_dbm", "snr_db", "throughput_mbps", "latency_ms", "event", "message"]
display_cols = [c for c in display_cols if c in df_table.columns]

def color_level(val):
    colors = {"ERROR": "color: #fc8181", "WARN": "color: #f6ad55", "INFO": "color: #68d391"}
    return colors.get(val, "")

st.dataframe(
    df_table[display_cols].sort_values("timestamp", ascending=False).head(200).style.applymap(
        color_level, subset=["level"]
    ),
    use_container_width=True,
    height=400,
)

st.caption(f"Showing up to 200 rows · {len(df_table):,} total matching entries")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("📡 Wireless Log Analyzer · Built for cellular & satellite test automation · LTE / 5G NR / Satellite")
