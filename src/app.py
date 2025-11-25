import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from monitor import ModelMonitor
import time

st.set_page_config(page_title="Phishing Model Monitor", layout="wide")

st.title("🎣 Phishing Model Monitoring Dashboard")
st.markdown("Real-time monitoring of data drift and model performance.")

# Initialize Monitor in Session State
if 'monitor' not in st.session_state:
    st.session_state.monitor = ModelMonitor()
    st.session_state.history = []

monitor = st.session_state.monitor

# Sidebar Configuration
st.sidebar.header("Simulation Controls")
batch_size = st.sidebar.slider("Batch Size", 100, 1000, 500)
drift_type = st.sidebar.selectbox("Inject Drift", [None, "data_drift", "concept_drift"], format_func=lambda x: "None (Normal)" if x is None else x.replace('_', ' ').title())

if st.sidebar.button("Process Next Batch"):
    with st.spinner("Processing batch..."):
        result = monitor.process_batch(batch_size=batch_size, drift_type=drift_type)
        
        if 'error' in result:
            st.error(result['error'])
        else:
            # Add timestamp
            result['timestamp'] = time.strftime("%H:%M:%S")
            st.session_state.history.insert(0, result) # Newest first

# Main Dashboard Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Feature Distributions (Reference vs Latest Batch)")
    
    if st.session_state.history:
        latest_result = st.session_state.history[0]
        latest_data = latest_result['data']
        ref_data = monitor.reference_data
        
        # Plot URL Length Distribution
        fig_len = go.Figure()
        fig_len.add_trace(go.Histogram(x=ref_data['url_length'], name='Reference', opacity=0.75, marker_color='blue'))
        fig_len.add_trace(go.Histogram(x=latest_data['url_length'], name='Latest Batch', opacity=0.75, marker_color='red'))
        fig_len.update_layout(barmode='overlay', title_text='URL Length Distribution')
        st.plotly_chart(fig_len, use_container_width=True)
        
        # Plot Special Chars
        fig_chars = go.Figure()
        fig_chars.add_trace(go.Histogram(x=ref_data['num_special_chars'], name='Reference', opacity=0.75, marker_color='blue'))
        fig_chars.add_trace(go.Histogram(x=latest_data['num_special_chars'], name='Latest Batch', opacity=0.75, marker_color='red'))
        fig_chars.update_layout(barmode='overlay', title_text='Special Characters Distribution')
        st.plotly_chart(fig_chars, use_container_width=True)
        
    else:
        st.info("No batches processed yet. Click 'Process Next Batch' in the sidebar.")

with col2:
    st.subheader("Drift Status")
    
    if st.session_state.history:
        latest = st.session_state.history[0]
        
        if latest['drift_detected']:
            st.error(f"🚨 Drift Detected at {latest['timestamp']}")
            if latest['retrained']:
                st.success("✅ Model Retrained Automatically")
        else:
            st.success(f"✅ System Healthy at {latest['timestamp']}")
            
        st.markdown("### Drift Report")
        report = latest['drift_report']
        
        # Create a nice dataframe for the report
        report_data = []
        for feature, res in report.items():
            report_data.append({
                "Feature": feature,
                "Test": res['test'],
                "P-Value": f"{res['p_value']:.4f}",
                "Drift?": "Yes" if res['drift_detected'] else "No"
            })
        
        st.table(pd.DataFrame(report_data))
        
    else:
        st.write("Waiting for data...")

# Historical Log
st.markdown("---")
st.subheader("Activity Log")
for item in st.session_state.history:
    status_icon = "🚨" if item['drift_detected'] else "✅"
    retrain_msg = " | 🔄 Retrained" if item['retrained'] else ""
    st.text(f"{item['timestamp']} - {status_icon} Batch Processed {retrain_msg}")
