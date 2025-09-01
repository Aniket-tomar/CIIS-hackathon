import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine

# --- Authentication Check ---
if not st.session_state.get('authenticated', False):
    st.error("You must be logged in to view this page.")
    st.stop()

# --- Page Configuration ---
st.set_page_config(page_title="Anomaly Detection", page_icon="🤖", layout="wide")
st.title("🤖 Anomaly Detection in IPDR Logs")

# --- Database Connection ---
try:
    db_engine = create_engine('sqlite:///ipdr_data.db')
except Exception as e:
    st.error(f"Could not connect to the database: {e}")
    st.stop()

# --- Adapted Anomaly Detection Functions ---

def create_features_from_db(df):
    """
    Creates new features from the data loaded from the database.
    This function is adapted to use columns available after our initial processing.
    """
    # Rename columns to match the expected names in the anomaly script
    if 'total_duration_seconds' in df.columns:
        df = df.rename(columns={'total_duration_seconds': 'session_duration'})
    if 'data_usage_mb' in df.columns:
        df = df.rename(columns={'data_usage_mb': 'bytes_transferred'}) # Using MB as a proxy for bytes

    # Time-based features
    df['session_start_time'] = pd.to_datetime(df['session_start_time'])
    df['hour_of_day'] = df['session_start_time'].dt.hour
    df['day_of_week'] = df['session_start_time'].dt.dayofweek

    # Statistical features (for a specific source_ip)
    df['avg_session_duration'] = df.groupby('source_ip')['session_duration'].transform('mean')
    df['std_session_duration'] = df.groupby('source_ip')['session_duration'].transform('std').fillna(0)
    df['avg_bytes_transferred'] = df.groupby('source_ip')['bytes_transferred'].transform('mean')
    df['std_bytes_transferred'] = df.groupby('source_ip')['bytes_transferred'].transform('std').fillna(0)
    
    # Count-based features
    df['session_start_hour'] = df['session_start_time'].dt.floor('H')
    df['unique_dest_count'] = df.groupby(['source_ip', 'session_start_hour'])['destination_ip'].transform('nunique')

    return df

def detect_anomalies(df, contamination_level):
    """
    Applies the Isolation Forest model to detect anomalies.
    """
    features = [
        'session_duration', 'bytes_transferred', 'hour_of_day', 'day_of_week',
        'avg_session_duration', 'std_session_duration', 'avg_bytes_transferred',
        'std_bytes_transferred', 'unique_dest_count'
    ]
    
    # Check if all required features are present
    missing_features = [f for f in features if f not in df.columns]
    if missing_features:
        st.error(f"The following required features could not be created or found: {', '.join(missing_features)}")
        return None

    df_cleaned = df.dropna(subset=features).copy()
    if df_cleaned.empty:
        st.warning("Not enough data to run anomaly detection after cleaning.")
        return None
        
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df_cleaned[features])
    
    model = IsolationForest(contamination=contamination_level, random_state=42)
    df_cleaned['anomaly'] = model.fit_predict(scaled_features)
    
    return df_cleaned, features

def plot_anomalies(df, x_param, y_param):
    """
    Creates a Matplotlib scatter plot to visualize anomalies.
    """
    anomalies = df[df['anomaly'] == -1]
    inliers = df[df['anomaly'] == 1]

    fig, ax = plt.subplots(figsize=(12, 8))
    
    ax.scatter(inliers[x_param], inliers[y_param], c='lightblue', s=20, label='Normal Data')
    ax.scatter(anomalies[x_param], anomalies[y_param], c='red', s=50, marker='x', label='Anomalies')
    
    ax.set_title(f'Anomaly Detection: {x_param.replace("_", " ").title()} vs. {y_param.replace("_", " ").title()}', fontsize=16)
    ax.set_xlabel(x_param.replace('_', ' ').title(), fontsize=12)
    ax.set_ylabel(y_param.replace('_', ' ').title(), fontsize=12)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)
    
    return fig

# --- Main Page UI and Logic ---

st.markdown("This page uses an **Isolation Forest** machine learning model to detect unusual patterns in your entire dataset. Adjust the model's sensitivity and run the analysis.")

# --- User Controls ---
contamination = st.slider(
    "Set Anomaly Sensitivity (Contamination)", 
    min_value=0.01, max_value=0.25, value=0.10, step=0.01,
    help="This value represents the expected proportion of anomalies in the data. Higher values will flag more data points as anomalous."
)

if st.button("Run Anomaly Detection", type="primary"):
    with st.spinner("Loading data from database..."):
        try:
            full_df = pd.read_sql("SELECT * FROM ipdr_logs", db_engine)
            if full_df.empty:
                st.warning("The database is empty. Please upload data first.")
                st.stop()
        except Exception as e:
            st.error(f"Failed to load data. Have you uploaded a file yet? Error: {e}")
            st.stop()
            
    with st.spinner("Step 1/3: Engineering features..."):
        df_with_features = create_features_from_db(full_df)

    with st.spinner("Step 2/3: Training model and detecting anomalies..."):
        results_df, features_used = detect_anomalies(df_with_features, contamination)
    
    with st.spinner("Step 3/3: Preparing results..."):
        if results_df is not None:
            st.session_state['anomaly_results'] = results_df
            st.session_state['features_used'] = features_used

# --- Display Results ---
if 'anomaly_results' in st.session_state:
    results = st.session_state['anomaly_results']
    anomalies = results[results['anomaly'] == -1]

    st.markdown("---")
    st.header("Detection Results")
    
    st.success(f"Analysis complete! Found **{len(anomalies)}** potential anomalies out of **{len(results)}** processed records.")
    
    st.subheader("Detected Anomalies")
    st.dataframe(anomalies[['source_ip', 'destination_ip', 'session_duration', 'bytes_transferred', 'user_number', 'session_start_time']])
    
    st.markdown("---")
    st.header("Visualize Anomalies")
    
    features = st.session_state['features_used']
    
    viz_col1, viz_col2 = st.columns(2)
    with viz_col1:
        x_axis = st.selectbox("Choose X-axis for plot", options=features, index=0)
    with viz_col2:
        y_axis = st.selectbox("Choose Y-axis for plot", options=features, index=1)
        
    st.info("The plot below shows normal data points in blue and highlights the detected anomalies in red.")
    
    # Generate and display the plot
    plot_fig = plot_anomalies(results, x_axis, y_axis)
    st.pyplot(plot_fig)
