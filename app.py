"""
Wireless Log Analyzer — Streamlit UI
Run: streamlit run app.py
"""
import sys
import os
import random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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

# ── Color palette ─────────────────────────────────────────────────────────────
BG      = "#080c14"
SURFACE = "#0d1117"
CARD    = "#111827"
BORDER  = "#1f2937"
MUTED   = "#374151"
TEXT    = "#f1f5f9"
SUB     = "#94a3b8"
ERR     = "#f87171"
WARN    = "#fbbf24"
OK      = "#34d399"
INFO    = "#60a5fa"
ACCENT  = "#818cf8"

TECH_COLORS  = {"LTE": INFO,  "5G_NR": OK,   "SATELLITE": WARN}
LEVEL_COLORS = {"INFO": INFO, "WARN": WARN,  "ERROR": ERR}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #080c14;
    color: #f1f5f9;
}
[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #1f2937;
}
[data-testid="stSidebar"] * { color: #f1f5f9 !important; }
.main .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }

.kpi {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
}
.kpi::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 12px 12px 0 0;
}
.kpi.blue::before   { background: #60a5fa; }
.kpi.red::before    { background: #f87171; }
.kpi.yellow::before { background: #fbbf24; }
.kpi.green::before  { background: #34d399; }
.kpi.purple::before { background: #818cf8; }
.kpi-lbl {
    font-size: .68rem; font-weight: 600;
    letter-spacing: .08em; text-transform: uppercase;
    color: #94a3b8; margin-bottom: 6px;
}
.kpi-val { font-size: 2rem; font-weight: 700; line-height: 1; color: #f1f5f9; }
.kpi-sub { font-size: .72rem; color: #94a3b8; margin-top: 5px; }
.badge {
    display: inline-block; font-size: .68rem; font-weight: 600;
    padding: 2px 8px; border-radius: 999px; margin-top: 5px;
}
.b-red    { background: rgba(248,113,113,.15); color: #f87171; }
.b-yellow { background: rgba(251,191,36,.15);  color: #fbbf24; }
.b-green  { background: rgba(52,211,153,.15);  color: #34d399; }
.b-blue   { background: rgba(96,165,250,.15);  color: #60a5fa; }

.sec {
    font-size: .68rem; font-weight: 600; letter-spacing: .1em;
    text-transform: uppercase; color: #94a3b8;
    margin: 24px 0 10px;
    display: flex; align-items: center; gap: 8px;
}
.sec::after { content: ''; flex: 1; height: 1px; background: #1f2937; }

.feat {
    background: #111827; border: 1px solid #1f2937;
    border-radius: 12px; padding: 20px;
}
.feat h4 { font-size: .85rem; font-weight: 600; color: #f1f5f9; margin-bottom: 8px; }
.feat p  { font-size: .78rem; color: #94a3b8; line-height: 1.6; margin: 0; }

div[data-testid="metric-container"] {
    background: #111827; border: 1px solid #1f2937;
    border-radius: 10px; padding: 14px 18px;
}
[data-testid="stMetricValue"] { font-size: 1.7rem !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] {
    font-size: .7rem !important; color: #94a3b8 !important;
    text-transform: uppercase; letter-spacing: .06em;
}
hr { border-color: #1f2937 !important; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #374151; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def kpi_card(col, label, value, color="blue", sub="", badge="", badge_cls="b-blue"):
    b = f'<span class="badge {badge_cls}">{badge}</span>' if badge else ""
    s = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    col.markdown(
        f'<div class="kpi {color}">'
        f'<div class="kpi-lbl">{label}</div>'
        f'<div class="kpi-val">{value}</div>'
        f'{s}{b}</div>',
        unsafe_allow_html=True,
    )

def sec_hdr(title):
    st.markdown(f'<div class="sec">{title}</div>', unsafe_allow_html=True)

def base_layout(fig, h=300):
    fig.update_layout(
        plot_bgcolor=BG, paper_bgcolor=CARD,
        font=dict(family="Inter", color=SUB, size=11),
        margin=dict(l=8, r=8, t=8, b=8), height=h,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            bgcolor="rgba(0,0,0,0)", font=dict(size=11),
        ),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickfont=dict(size=10)),
    )
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div style="padding:6px 0 14px">'
        f'<div style="font-size:1.1rem;font-weight:700;color:{TEXT}">📡 Wireless Log Analyzer</div>'
        f'<div style="font-size:.73rem;color:{SUB};margin-top:2px">Cellular & Satellite Test Automation</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown(
        f'<div style="font-size:.68rem;font-weight:600;letter-spacing:.08em;'
        f'text-transform:uppercase;color:{SUB};margin-bottom:6px">DATA SOURCE</div>',
        unsafe_allow_html=True,
    )
    data_source = st.radio(
        "", ["Generate synthetic logs", "Upload a log file"],
        index=0, label_visibility="collapsed",
    )

    uploaded_file = None
    if data_source == "Generate synthetic logs":
        log_count = st.slider("Log entries", 100, 2000, 500, step=100)
        seed = st.number_input("Random seed (0 = random)", 0, 9999, 0)
        go_btn = st.button("⚡  Generate & Analyze", type="primary", use_container_width=True)
    else:
        uploaded_file = st.file_uploader("Upload .jsonl file", type=["jsonl", "json"])
        go_btn = st.button("🔍  Analyze", type="primary", use_container_width=True)

    st.divider()
    st.markdown(
        f'<div style="font-size:.68rem;font-weight:600;letter-spacing:.08em;'
        f'text-transform:uppercase;color:{SUB};margin-bottom:6px">FILTERS</div>',
        unsafe_allow_html=True,
    )
    tech_filter  = st.multiselect("Technology", ["LTE", "5G_NR", "SATELLITE"], default=["LTE", "5G_NR", "SATELLITE"])
    level_filter = st.multiselect("Log Level",  ["INFO", "WARN", "ERROR"],     default=["INFO", "WARN", "ERROR"])
    st.divider()
    st.markdown(
        f'<div style="font-size:.7rem;color:{SUB}">LTE · 5G NR · Satellite<br>PHY / MAC / RRC / NAS</div>',
        unsafe_allow_html=True,
    )


# ── Session state ─────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = None
if "df" not in st.session_state:
    st.session_state.df = None


def load(path):
    r  = analyze(path)
    df = pd.DataFrame(r["raw_logs"])
    df["timestamp"]  = pd.to_datetime(df["timestamp"])
    df["latency_ms"] = df["latency_ms"].apply(lambda x: None if x >= 9000 else x)
    return r, df


if go_btn:
    with st.spinner("Analyzing..."):
        if data_source == "Generate synthetic logs":
            if seed > 0:
                random.seed(seed)
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthetic_logs.jsonl")
            generate_logs(num_entries=log_count, output_file="synthetic_logs.jsonl")
            st.session_state.results, st.session_state.df = load(p)
        else:
            if not uploaded_file:
                st.warning("Please upload a log file first.")
                st.stop()
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_uploaded.jsonl")
            with open(p, "wb") as f:
                f.write(uploaded_file.read())
            st.session_state.results, st.session_state.df = load(p)

# ── Landing page ──────────────────────────────────────────────────────────────
if st.session_state.results is None:
    st.markdown(
        f'<div style="padding:32px 0 20px">'
        f'<div style="font-size:2rem;font-weight:700;color:{TEXT};letter-spacing:-.02em">📡 Wireless Log Analyzer</div>'
        f'<div style="font-size:.95rem;color:{SUB};margin-top:6px;max-width:600px">'
        f'Automated anomaly detection for LTE, 5G NR, and Satellite connectivity stacks. '
        f'Generate synthetic logs or upload your own to get started.'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="feat"><h4>🔍 Detects</h4><p>'
            'Hard failures (ERROR)<br>Signal degradation<br>'
            'Ping-pong handoffs<br>Consecutive failure streaks'
            '</p></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="feat"><h4>📶 Covers</h4><p>'
            'LTE — B1, B2, B4, B12, B17, B66<br>'
            '5G NR — n41, n77, n260, n261<br>'
            'Satellite — S-BAND, L-BAND<br>'
            'Layers: PHY / MAC / RRC / NAS'
            '</p></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="feat"><h4>📊 Metrics</h4><p>'
            'RSSI & SNR over time<br>Throughput trends<br>'
            'Latency distribution<br>Per-band failure breakdown'
            '</p></div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div style="margin-top:28px;font-size:.8rem;color:{SUB}">← Use the sidebar to generate or upload logs</div>',
        unsafe_allow_html=True,
    )
    st.stop()


# ── Apply filters ─────────────────────────────────────────────────────────────
df_full = st.session_state.df.copy()
df = df_full[
    df_full["technology"].isin(tech_filter) &
    df_full["level"].isin(level_filter)
].copy()

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="display:flex;align-items:baseline;gap:12px;padding-bottom:4px">'
    f'<div style="font-size:1.4rem;font-weight:700;color:{TEXT}">📡 Dashboard</div>'
    f'<div style="font-size:.78rem;color:{SUB}">{len(df):,} of {len(df_full):,} entries</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── KPI row ───────────────────────────────────────────────────────────────────
total     = len(df)
errors    = len(df[df["level"] == "ERROR"])
warns     = len(df[df["level"] == "WARN"])
crit_rssi = len(df[df["rssi_dbm"] < -105])
high_lat  = len(df[(df["latency_ms"].notna()) & (df["latency_ms"] > 500)])
pp        = len(df[df["event"] == "PING_PONG_HANDOFF"])
err_pct   = f"{errors / total * 100:.1f}%" if total else "0%"

k1, k2, k3, k4, k5, k6 = st.columns(6)
kpi_card(k1, "Total Entries",    f"{total:,}",     "blue",   sub="log entries")
kpi_card(k2, "Failures",         f"{errors:,}",    "red",    badge=err_pct, badge_cls="b-red")
kpi_card(k3, "Warnings",         f"{warns:,}",     "yellow", sub="degradation + handoff")
kpi_card(k4, "Critical RSSI",    f"{crit_rssi:,}", "purple", sub="below -105 dBm")
kpi_card(k5, "High Latency",     f"{high_lat:,}",  "yellow", sub="above 500 ms")
kpi_card(k6, "Ping-Pong Events", f"{pp:,}",        "red",    sub="oscillating handoffs")

st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

# ── Timeline + Donut ──────────────────────────────────────────────────────────
sec_hdr("EVENT TIMELINE")
cl, cr = st.columns([3, 1])

with cl:
    df_t = df.copy()
    df_t["minute"] = df_t["timestamp"].dt.floor("1min")
    tl = df_t.groupby(["minute", "level"]).size().reset_index(name="count")
    fig = px.bar(
        tl, x="minute", y="count", color="level",
        color_discrete_map=LEVEL_COLORS,
        labels={"minute": "", "count": "Events", "level": "Level"},
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(base_layout(fig, 260), use_container_width=True)

with cr:
    lc = df["level"].value_counts()
    fig2 = go.Figure(
        go.Pie(
            labels=lc.index, values=lc.values, hole=0.6,
            marker_colors=[LEVEL_COLORS.get(l, "#aaa") for l in lc.index],
            textinfo="label+percent", textfont=dict(size=11, color=TEXT),
        )
    )
    fig2.update_layout(
        paper_bgcolor=CARD, showlegend=False,
        margin=dict(l=8, r=8, t=8, b=8), height=260,
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── RF Metrics ────────────────────────────────────────────────────────────────
sec_hdr("RF METRICS OVER TIME")
t1, t2, t3, t4 = st.tabs(["RSSI (dBm)", "SNR (dB)", "Throughput (Mbps)", "Latency (ms)"])

def scatter_chart(col, ylabel, threshold=None, tlabel=""):
    d = df[df[col].notna()].sort_values("timestamp")
    f = px.scatter(
        d, x="timestamp", y=col, color="technology",
        color_discrete_map=TECH_COLORS, opacity=0.55,
        labels={"timestamp": "", col: ylabel},
    )
    if threshold:
        f.add_hline(
            y=threshold, line_dash="dash", line_color=ERR,
            annotation_text=tlabel, annotation_font_color=ERR,
            annotation_position="top left",
        )
    f.update_traces(marker=dict(size=5))
    return base_layout(f, 290)

with t1:
    st.plotly_chart(scatter_chart("rssi_dbm", "RSSI (dBm)", -105, "Critical -105 dBm"), use_container_width=True)
with t2:
    st.plotly_chart(scatter_chart("snr_db", "SNR (dB)", 2, "Poor SNR < 2 dB"), use_container_width=True)
with t3:
    d = df[df["throughput_mbps"] > 0].sort_values("timestamp")
    f = px.line(
        d, x="timestamp", y="throughput_mbps", color="technology",
        color_discrete_map=TECH_COLORS,
        labels={"timestamp": "", "throughput_mbps": "Mbps"},
    )
    st.plotly_chart(base_layout(f, 290), use_container_width=True)
with t4:
    d = df[df["latency_ms"].notna()]
    f = px.histogram(
        d, x="latency_ms", color="technology",
        color_discrete_map=TECH_COLORS, nbins=40, opacity=0.75, barmode="overlay",
        labels={"latency_ms": "Latency (ms)"},
    )
    f.add_vline(
        x=500, line_dash="dash", line_color=ERR,
        annotation_text="500 ms threshold", annotation_font_color=ERR,
    )
    st.plotly_chart(base_layout(f, 290), use_container_width=True)

# ── Failure Analysis ──────────────────────────────────────────────────────────
sec_hdr("FAILURE ANALYSIS")
ca, cb, cc = st.columns(3)

with ca:
    st.markdown(
        f'<div style="font-size:.75rem;font-weight:600;color:{SUB};margin-bottom:6px">BY TECHNOLOGY</div>',
        unsafe_allow_html=True,
    )
    d = df[df["level"] == "ERROR"]["technology"].value_counts().reset_index()
    d.columns = ["technology", "count"]
    f = px.bar(
        d, x="count", y="technology", orientation="h",
        color="technology", color_discrete_map=TECH_COLORS,
    )
    f.update_layout(showlegend=False, yaxis_title="", xaxis_title="Failures")
    st.plotly_chart(base_layout(f, 240), use_container_width=True)

with cb:
    st.markdown(
        f'<div style="font-size:.75rem;font-weight:600;color:{SUB};margin-bottom:6px">TOP FAILURE TYPES</div>',
        unsafe_allow_html=True,
    )
    skip = {"NORMAL_OPERATION", "HANDOFF_INITIATED", "SIGNAL_DEGRADATION", "PING_PONG_HANDOFF"}
    d = df[(df["level"] == "ERROR") & (~df["event"].isin(skip))]["event"].value_counts().head(7).reset_index()
    d.columns = ["event", "count"]
    f = px.bar(d, x="count", y="event", orientation="h", color_discrete_sequence=[ERR])
    f.update_layout(showlegend=False, yaxis_title="", xaxis_title="Count")
    st.plotly_chart(base_layout(f, 240), use_container_width=True)

with cc:
    st.markdown(
        f'<div style="font-size:.75rem;font-weight:600;color:{SUB};margin-bottom:6px">BY BAND</div>',
        unsafe_allow_html=True,
    )
    d = df[df["level"] == "ERROR"].copy()
    d["band_key"] = d["technology"] + " " + d["band"]
    d = d["band_key"].value_counts().head(8).reset_index()
    d.columns = ["band", "count"]
    f = px.bar(d, x="count", y="band", orientation="h", color_discrete_sequence=[ACCENT])
    f.update_layout(showlegend=False, yaxis_title="", xaxis_title="Failures")
    st.plotly_chart(base_layout(f, 240), use_container_width=True)

# ── Avg RF Metrics ────────────────────────────────────────────────────────────
sec_hdr("AVERAGE RF METRICS")
m1, m2, m3, m4 = st.columns(4)
dh = df[df["latency_ms"].notna()]
avg_rssi = round(dh["rssi_dbm"].mean(), 1) if len(dh) else 0
avg_snr  = round(dh["snr_db"].mean(), 1)   if len(dh) else 0
avg_tp   = round(df[df["throughput_mbps"] > 0]["throughput_mbps"].mean(), 1) if len(df) else 0
avg_lat  = round(dh["latency_ms"].mean(), 1) if len(dh) else 0
m1.metric("Avg RSSI",       f"{avg_rssi} dBm", help="Target > -95 dBm")
m2.metric("Avg SNR",        f"{avg_snr} dB",   help="Target > 10 dB")
m3.metric("Avg Throughput", f"{avg_tp} Mbps",  help="Higher is better")
m4.metric("Avg Latency",    f"{avg_lat} ms",   help="Target < 200 ms")

# ── Handoff Sankey ────────────────────────────────────────────────────────────
sec_hdr("HANDOFF FLOW")
dho = df[df["event"] == "HANDOFF_INITIATED"].copy()
if "target_technology" in dho.columns and len(dho):
    dho = dho.dropna(subset=["target_technology"])
    sd  = dho.groupby(["technology", "target_technology"]).size().reset_index(name="count")
    nodes = list(set(sd["technology"].tolist() + sd["target_technology"].tolist()))
    ni    = {n: i for i, n in enumerate(nodes)}
    fig_s = go.Figure(
        go.Sankey(
            node=dict(
                pad=20, thickness=18, label=nodes,
                color=[TECH_COLORS.get(n, "#aaa") for n in nodes],
            ),
            link=dict(
                source=[ni[r["technology"]] for _, r in sd.iterrows()],
                target=[ni[r["target_technology"]] for _, r in sd.iterrows()],
                value=sd["count"].tolist(),
                color="rgba(96,165,250,0.2)",
            ),
        )
    )
    fig_s.update_layout(
        paper_bgcolor=CARD, font=dict(family="Inter", color=TEXT, size=12),
        margin=dict(l=8, r=8, t=8, b=8), height=280,
    )
    st.plotly_chart(fig_s, use_container_width=True)
else:
    st.markdown(
        f'<div style="color:{SUB};font-size:.82rem;padding:12px 0">No handoff events in current selection.</div>',
        unsafe_allow_html=True,
    )

# ── Log Explorer ──────────────────────────────────────────────────────────────
sec_hdr("LOG EXPLORER")
s1, s2, s3 = st.columns([2, 2, 2])
with s1:
    search = st.text_input("Search", placeholder="FAILURE, RRC, n260…")
with s2:
    ev_sel = st.multiselect("Event", sorted(df["event"].unique()), default=[])
with s3:
    ly_sel = st.multiselect("Layer", sorted(df["layer"].dropna().unique()) if "layer" in df.columns else [], default=[])

dt = df.copy()
if search:
    dt = dt[dt["message"].str.contains(search, case=False, na=False)]
if ev_sel:
    dt = dt[dt["event"].isin(ev_sel)]
if ly_sel:
    dt = dt[dt["layer"].isin(ly_sel)]

cols = [
    "timestamp", "level", "technology", "band", "layer", "state",
    "rssi_dbm", "snr_db", "throughput_mbps", "latency_ms", "event", "message",
]
cols = [c for c in cols if c in dt.columns]

def clr(v):
    return {"ERROR": "color:#f87171", "WARN": "color:#fbbf24", "INFO": "color:#34d399"}.get(v, "")

st.dataframe(
   dt[cols].sort_values("timestamp", ascending=False).head(200).style.map(clr, subset=["level"]),
    use_container_width=True, height=380,
)
st.markdown(
    f'<div style="font-size:.72rem;color:{SUB};margin-top:4px">Showing up to 200 rows · {len(dt):,} matching</div>',
    unsafe_allow_html=True,
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f'<div style="font-size:.72rem;color:{SUB};text-align:center">'
    f'📡 Wireless Log Analyzer · LTE / 5G NR / Satellite · Built for cellular & satellite test automation'
    f'</div>',
    unsafe_allow_html=True,
)
