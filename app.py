import streamlit as st
import json
import time
import pandas as pd
from datetime import datetime
from triage import triage_alert
from report import generate_pdf_report

st.set_page_config(
    page_title="SOC Triage AI",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Inter:wght@300;400;500;600&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #020B18;
    color: #CBD5E1;
}
.stApp {
    background-color: #020B18;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(0,80,160,0.07) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 20%, rgba(0,180,255,0.04) 0%, transparent 50%);
}
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #020B18; }
::-webkit-scrollbar-thumb { background: #1E3A5F; border-radius: 2px; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #030F1E 0%, #041525 100%);
    border-right: 1px solid #0D2137;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {
    color: #94A3B8 !important;
    font-size: 13px !important;
}
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #041525 0%, #061C30 100%);
    border: 1px solid #0D2137;
    border-radius: 8px;
    padding: 1rem;
    transition: border-color 0.3s;
}
[data-testid="stMetric"]:hover { border-color: #1A6BAA; }
[data-testid="stMetricLabel"] {
    color: #64748B !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stMetricValue"] {
    color: #E2E8F0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.8rem !important;
}
[data-testid="stExpander"] {
    background: #041525;
    border: 1px solid #0D2137;
    border-radius: 8px;
    margin-bottom: 8px;
    transition: border-color 0.2s, box-shadow 0.2s;
}
[data-testid="stExpander"]:hover {
    border-color: #1A5C8A;
    box-shadow: 0 0 16px rgba(0,120,200,0.08);
}
[data-testid="stExpander"] summary {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #CBD5E1 !important;
    padding: 0.85rem 1rem !important;
}
.stButton > button {
    background: linear-gradient(135deg, #0A3A5C, #0D4F7C);
    color: #7EC8E3 !important;
    border: 1px solid #1A6BAA;
    border-radius: 6px;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.04em;
    transition: all 0.2s;
    width: 100%;
    padding: 0.5rem 1rem;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #0D4F7C, #1565A0);
    color: #BAE6FD !important;
    box-shadow: 0 0 20px rgba(0,150,255,0.2);
    border-color: #2E86C1;
}
[data-testid="stFileUploaderDropzone"] {
    background: #041525 !important;
    border: 1px dashed #1A3A5C !important;
}
[data-testid="stFileUploaderDropzone"] * {
    background: #041525 !important;
    color: #64748B !important;
}
.stProgress > div > div {
    background: linear-gradient(90deg, #0D4F7C, #00B4D8);
    box-shadow: 0 0 8px rgba(0,180,216,0.4);
}
hr { border-color: #0D2137 !important; }
code {
    background: #0A1F33 !important;
    color: #7DD3FC !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="
    background: linear-gradient(135deg, #030F1E 0%, #041525 50%, #030F1E 100%);
    border: 1px solid #0D2137;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
">
    <div style="position:absolute;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,transparent,#1A6BAA,#00B4D8,#1A6BAA,transparent);"></div>
    <div style="display:flex;align-items:center;gap:1.25rem;flex-wrap:wrap;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;color:#1A6BAA;line-height:1;">[SOC]</div>
        <div style="flex:1;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:1.4rem;font-weight:500;color:#E2E8F0;letter-spacing:0.04em;">SOC Alert Triage Assistant</div>
            <div style="font-family:'Inter',sans-serif;font-size:13px;color:#475569;margin-top:4px;">AI-powered first-pass security alert analysis &middot; Llama 3.3 70B via Groq</div>
        </div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#22C55E;background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.25);border-radius:6px;padding:6px 14px;letter-spacing:0.06em;">[ ONLINE ]</div>
    </div>
</div>
""", unsafe_allow_html=True)

SEVERITY_CONFIG = {
    "CRITICAL": {"color": "#F87171", "bg": "rgba(248,113,113,0.07)"},
    "HIGH":     {"color": "#FB923C", "bg": "rgba(251,146,60,0.07)"},
    "MEDIUM":   {"color": "#FBBF24", "bg": "rgba(251,191,36,0.07)"},
    "LOW":      {"color": "#4ADE80", "bg": "rgba(74,222,128,0.07)"},
    "INFO":     {"color": "#38BDF8", "bg": "rgba(56,189,248,0.07)"},
    "ERROR":    {"color": "#64748B", "bg": "rgba(100,116,139,0.07)"},
}

with st.sidebar:
    st.markdown("""
    <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:600;
    color:#475569;letter-spacing:0.12em;text-transform:uppercase;
    margin-bottom:1rem;padding-bottom:0.75rem;border-bottom:1px solid #0D2137;">
    Alert Feed
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload alerts (JSON or CSV)", type=["json", "csv"])

    st.markdown("""
    <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:600;
    color:#475569;letter-spacing:0.12em;text-transform:uppercase;
    margin-top:1.5rem;margin-bottom:0.6rem;">
    Expected Format
    </div>
    <div style="background:#041525;border:1px solid #0D2137;border-radius:6px;
    padding:0.85rem 1rem;font-family:'JetBrains Mono',monospace;font-size:12px;
    line-height:1.8;color:#475569;">
    <span style="color:#475569">{</span><br>
    &nbsp;&nbsp;<span style="color:#7DD3FC">"alert_id"</span>: <span style="color:#86EFAC">"ALT-001"</span>,<br>
    &nbsp;&nbsp;<span style="color:#7DD3FC">"alert_type"</span>: <span style="color:#86EFAC">"Brute Force"</span>,<br>
    &nbsp;&nbsp;<span style="color:#7DD3FC">"description"</span>: <span style="color:#86EFAC">"..."</span>,<br>
    &nbsp;&nbsp;<span style="color:#7DD3FC">"source_ip"</span>: <span style="color:#86EFAC">"x.x.x.x"</span>,<br>
    &nbsp;&nbsp;<span style="color:#7DD3FC">"hostname"</span>: <span style="color:#86EFAC">"server-01"</span><br>
    <span style="color:#475569">}</span>
    </div>
    <div style="margin-top:2rem;padding-top:1rem;border-top:1px solid #0D2137;
    font-family:'JetBrains Mono',monospace;font-size:10px;color:#1E3A5F;text-align:center;">
    soc-triage-ai v1.2.0
    </div>
    """, unsafe_allow_html=True)

# --- Main Logic ---
if uploaded_file is None:
    st.markdown("""
    <div style="background:#041525;border:1px dashed #1A3A5C;border-radius:10px;
    padding:2.5rem;text-align:center;margin-bottom:1.5rem;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:1.5rem;
        color:#1A3A5C;margin-bottom:0.75rem;">[  ]</div>
        <div style="font-family:'Inter',sans-serif;font-weight:500;
        color:#CBD5E1;font-size:15px;margin-bottom:6px;">Awaiting Alert Data</div>
        <div style="color:#475569;font-size:13px;">
        Upload a JSON or CSV file, or run on the built-in sample alerts</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(">> Run on Sample Alerts"):
        with open("sample_alerts/alerts.json") as f:
            alerts = json.load(f)
        st.session_state["alerts"] = alerts
        st.session_state["run_triage"] = True
        st.rerun()

else:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        alerts = df.to_dict(orient="records")
    else:
        alerts = json.load(uploaded_file)

    st.session_state["alerts"] = alerts
    st.markdown(f"""
    <div style="background:rgba(34,197,94,0.05);border:1px solid rgba(34,197,94,0.2);
    border-radius:8px;padding:0.85rem 1.25rem;margin-bottom:1rem;
    font-family:'Inter',sans-serif;font-size:14px;color:#4ADE80;">
    [OK] Loaded <strong>{len(alerts)} alerts</strong> - ready for triage
    </div>
    """, unsafe_allow_html=True)

    if st.button(">> Initiate Triage"):
        st.session_state["run_triage"] = True
        st.rerun()

# --- Triage Engine ---
if st.session_state.get("run_triage"):
    alerts = st.session_state.get("alerts", [])

    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace;font-size:13px;
    color:#38BDF8;margin-bottom:1rem;letter-spacing:0.03em;">
    &gt; Analyzing {len(alerts)} alerts...
    </div>
    """, unsafe_allow_html=True)

    progress = st.progress(0)
    status_box = st.empty()
    results = []

    for i, alert in enumerate(alerts):
        alert_id = alert.get("alert_id", f"ALT-{i+1}")
        status_box.markdown(f"""
        <div style="font-family:'JetBrains Mono',monospace;font-size:12px;
        color:#475569;padding:4px 0;letter-spacing:0.02em;">
        &gt; Processing {alert_id} - {alert.get('alert_type','UNKNOWN')}
        </div>
        """, unsafe_allow_html=True)

        try:
            result = triage_alert(alert)
            result["alert_id"] = alert_id
            result["original_type"] = alert.get("alert_type", "N/A")
            result["hostname"] = alert.get("hostname", "N/A")
        except Exception as e:
            result = {
                "alert_id": alert_id,
                "severity": "ERROR",
                "category": "N/A",
                "confidence": 0,
                "summary": str(e),
                "recommended_action": "Manual review required",
                "is_false_positive": False,
                "false_positive_reason": "N/A",
                "original_type": alert.get("alert_type", "N/A"),
                "hostname": alert.get("hostname", "N/A")
            }

        results.append(result)
        progress.progress((i + 1) / len(alerts))
        time.sleep(0.1)

    status_box.empty()
    progress.empty()
    st.session_state["results"] = results
    st.session_state["run_triage"] = False
    st.rerun()

# --- Results ---
if st.session_state.get("results"):
    results = st.session_state["results"]
    severity_counts = {}
    for r in results:
        s = r.get("severity", "ERROR")
        severity_counts[s] = severity_counts.get(s, 0) + 1
    fp_count = sum(1 for r in results if str(r.get("is_false_positive","")).lower() == "true")

    st.markdown("""
    <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:600;
    color:#475569;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.75rem;">
    Threat Assessment Overview
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("CRITICAL", severity_counts.get("CRITICAL", 0))
    col2.metric("HIGH", severity_counts.get("HIGH", 0))
    col3.metric("MEDIUM", severity_counts.get("MEDIUM", 0))
    col4.metric("LOW", severity_counts.get("LOW", 0))
    col5.metric("FALSE POS", fp_count)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:600;
    color:#475569;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.75rem;">
    Alert Triage Results
    </div>
    """, unsafe_allow_html=True)

    all_severities = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "ERROR"]
    selected = st.selectbox(
        "Filter by severity",
        all_severities,
        index=0,
        label_visibility="collapsed"
    )

    filtered = results if selected == "ALL" else [r for r in results if r.get("severity") == selected]

    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#475569;
    margin-bottom:0.75rem;letter-spacing:0.04em;">
    Showing {len(filtered)} of {len(results)} alerts
    </div>
    """, unsafe_allow_html=True)

    for r in filtered:
        sev = r.get("severity", "ERROR")
        cfg = SEVERITY_CONFIG.get(sev, SEVERITY_CONFIG["ERROR"])

        with st.expander(f"[{sev}]  {r.get('alert_id')}  --  {r.get('original_type')}"):
            st.markdown(f"""
            <div style="background:{cfg['bg']};border-left:3px solid {cfg['color']};
            border-radius:0 8px 8px 0;padding:1.25rem 1.5rem;margin-bottom:0.5rem;">
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1.5rem;margin-bottom:1.25rem;">
                    <div>
                        <div style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.1em;font-family:'Inter',sans-serif;margin-bottom:5px;">Severity</div>
                        <div style="color:{cfg['color']};font-size:14px;font-weight:600;font-family:'JetBrains Mono',monospace;">{sev}</div>
                    </div>
                    <div>
                        <div style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.1em;font-family:'Inter',sans-serif;margin-bottom:5px;">Category</div>
                        <div style="color:#CBD5E1;font-size:14px;">{r.get('category','N/A')}</div>
                    </div>
                    <div>
                        <div style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.1em;font-family:'Inter',sans-serif;margin-bottom:5px;">Confidence</div>
                        <div style="color:#38BDF8;font-size:14px;font-weight:600;font-family:'JetBrains Mono',monospace;">{r.get('confidence','N/A')}%</div>
                    </div>
                </div>
                <div style="margin-bottom:1rem;">
                    <div style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:5px;">Hostname</div>
                    <code style="font-size:13px;padding:2px 8px;border-radius:4px;">{r.get('hostname','N/A')}</code>
                </div>
                <div style="margin-bottom:1rem;">
                    <div style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">Analysis</div>
                    <div style="color:#CBD5E1;font-size:14px;line-height:1.65;">{r.get('summary','N/A')}</div>
                </div>
                <div>
                    <div style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">Recommended Action</div>
                    <div style="color:#7DD3FC;font-size:14px;line-height:1.65;">&gt; {r.get('recommended_action','N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if str(r.get("is_false_positive","")).lower() == "true":
                st.markdown(f"""
                <div style="background:rgba(251,191,36,0.05);border:1px solid rgba(251,191,36,0.2);
                border-radius:6px;padding:0.75rem 1.25rem;font-size:13px;color:#FBBF24;
                font-family:'Inter',sans-serif;">
                [WARNING] Possible False Positive -- {r.get('false_positive_reason','N/A')}
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:600;
    color:#475569;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.75rem;">
    Export Report
    </div>
    """, unsafe_allow_html=True)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    report_lines = [
        "# SOC Triage Report\n",
        f"**Generated:** {timestamp}",
        f"**Total Alerts Analyzed:** {len(results)}\n"
    ]
    for r in results:
        report_lines.append(f"## [{r.get('severity')}] {r.get('alert_id')} - {r.get('original_type')}")
        report_lines.append(f"- **Host:** {r.get('hostname')}")
        report_lines.append(f"- **Category:** {r.get('category')}")
        report_lines.append(f"- **Confidence:** {r.get('confidence')}%")
        report_lines.append(f"- **Analysis:** {r.get('summary')}")
        report_lines.append(f"- **Action:** {r.get('recommended_action')}\n")

    pdf_bytes = generate_pdf_report(results)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            label="Download Report (.md)",
            data="\n".join(report_lines),
            file_name="soc_triage_report.md",
            mime="text/markdown"
        )
    with col2:
        st.download_button(
            label="Download Report (.pdf)",
            data=pdf_bytes,
            file_name="soc_triage_report.pdf",
            mime="application/pdf"
        )
    with col3:
        if st.button("Clear & Reset"):
            st.session_state.clear()
            st.rerun()