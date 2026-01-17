import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os

# Set page configuration
st.set_page_config(page_title="Decision Intelligence Dashboard", layout="wide")

# --- PATH LOGIC FOR CLOUD DEPLOYMENT ---
# This finds the directory where app.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))

def get_data_path(filename):
    return os.path.join(current_dir, filename)

# Load Data
@st.cache_data
def load_data():
    # Use absolute paths to ensure the cloud server finds the files
    forecast_df = pd.read_csv(get_data_path('revenue_forecast_scenarios.csv'))
    roi_df = pd.read_csv(get_data_path('roi_simulation_results.csv'))
    segment_df = pd.read_csv(get_data_path('segment_decision_summary.csv'))
    
    # Preprocessing
    forecast_df['Date'] = pd.to_datetime(forecast_df['Date'], dayfirst=True)
    return forecast_df, roi_df, segment_df

# --- HEADER SECTION (LOGO AND TITLE) ---
col_logo, col_title = st.columns([1, 4])

with col_logo:
    try:
        logo_img = Image.open(get_data_path('Mu_sigma_logo.jpg'))
        st.image(logo_img, width=150)
    except Exception:
        st.info("Logo placeholder")

with col_title:
    st.markdown("""
        <h1 style='margin-top:-10px;'>Decision Intelligence Dashboard</h1>
        <p style='font-size:1.2rem; color:gray;'>Revenue Growth & Risk Management</p>
    """, unsafe_allow_html=True)

st.markdown("---")

# Safety check for data loading
try:
    forecast_df, roi_df, segment_df = load_data()
except Exception as e:
    st.error(f"Could not find data files in {current_dir}. Error: {e}")
    st.stop()

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Executive Summary", "Customer Segmentation", "Revenue Forecasting", "ROI Analysis"])

# --- PAGE 1: EXECUTIVE SUMMARY ---
if page == "Executive Summary":
    st.header("📊 Executive Summary")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Customers", f"{int(segment_df['Customer_Count'].sum()):,}")
    m2.metric("Projected Gain", f"${roi_df['Projected_Gain'].sum():,.0f}")
    m3.metric("Avg ROI", f"{roi_df['ROI'].mean():,.1f}x")
    m4.metric("Total Investment", f"${roi_df['Investment'].sum():,.0f}")

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Customer Strategy Distribution")
        fig_seg = px.pie(segment_df, values='Customer_Count', names='Decision_Action', hole=0.4)
        st.plotly_chart(fig_seg, use_container_width=True)
    
    with c2:
        st.subheader("ROI by Segment")
        fig_roi = px.bar(roi_df.sort_values('ROI', ascending=False), x='Segment', y='ROI', color='ROI', color_continuous_scale='Viridis')
        st.plotly_chart(fig_roi, use_container_width=True)

# --- PAGE 2: CUSTOMER SEGMENTATION ---
elif page == "Customer Segmentation":
    st.header("👥 Customer Segmentation Analysis")
    st.dataframe(segment_df.style.background_gradient(subset=['Avg_Monetary'], cmap='Blues'), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Recency vs Frequency")
        fig = px.scatter(segment_df, x='Avg_Recency', y='Avg_Frequency', size='Customer_Count', color='Decision_Action', hover_name='Decision_Action')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Revenue per Cluster")
        fig2 = px.bar(segment_df, x='Cluster', y='Avg_Monetary', color='Decision_Action')
        st.plotly_chart(fig2, use_container_width=True)

# --- PAGE 3: REVENUE FORECASTING ---
elif page == "Revenue Forecasting":
    st.header("📈 Revenue Forecasting Scenarios")
    scenarios = st.multiselect("Select Scenarios", ['Base_Forecast', 'Best_Case', 'Worst_Case'], default=['Base_Forecast'])

    fig = go.Figure()
    # Add Confidence Interval
    fig.add_trace(go.Scatter(
        x=forecast_df['Date'].tolist() + forecast_df['Date'].tolist()[::-1],
        y=forecast_df['Upper_CI'].tolist() + forecast_df['Lower_CI'].tolist()[::-1],
        fill='toself', fillcolor='rgba(0,100,80,0.1)', line_color='rgba(255,255,255,0)', name='95% CI'
    ))
    
    for s in scenarios:
        fig.add_trace(go.Scatter(x=forecast_df['Date'], y=forecast_df[s], name=s, line=dict(width=3)))
    
    fig.update_layout(xaxis_title="Timeline", yaxis_title="Revenue ($)", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE 4: ROI ANALYSIS ---
elif page == "ROI Analysis":
    st.header("💰 Investment & ROI Simulation")
    fig = go.Figure(data=[
        go.Bar(name='Investment', x=roi_df['Segment'], y=roi_df['Investment']),
        go.Bar(name='Projected Gain', x=roi_df['Segment'], y=roi_df['Projected_Gain'])
    ])
    fig.update_layout(barmode='group')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    selected_segment = st.selectbox("Deep Dive into Segment", roi_df['Segment'].unique())
    seg_data = roi_df[roi_df['Segment'] == selected_segment].iloc[0]
    
    d1, d2, d3 = st.columns(3)
    d1.metric("ROI Ratio", f"{seg_data['ROI']:.2f}x")
    d2.metric("Break-Even Target", f"${seg_data['BreakEven_Revenue']:,.2f}")
    eff = seg_data['Projected_Gain'] / seg_data['Investment']
    d3.metric("Efficiency Score", f"{eff:.1f}x")
