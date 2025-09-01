import streamlit as st
import pandas as pd
import requests
import socket
import time
from sqlalchemy import create_engine
import streamlit as st

# --- Authentication Check ---
if not st.session_state.get('authenticated', False):
    st.error("You must be logged in to view this page.")
    st.stop()

# --- Database Setup ---
# This creates a connection to a local SQLite database file.
db_engine = create_engine('sqlite:///ipdr_data.db')

# --- Core Processing Logic ---
@st.cache_data
def get_ip_details(ip_address, api_token=""): # Default empty token
    if not ip_address or pd.isna(ip_address) or ip_address.startswith(('192.168.', '10.', '172.16.')):
        return {'country': 'Local Network', 'state': 'N/A', 'city': 'N/A', 'latitude': None, 'longitude': None}
    url = f"https://ipinfo.io/{ip_address}/json"
    headers = {'Authorization': f'Bearer {api_token}'} if api_token else {}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        loc = data.get('loc', ',').split(',')
        return {
            'country': data.get('country', 'Unknown'), 'state': data.get('region', 'Unknown'),
            'city': data.get('city', 'Unknown'), 'latitude': loc[0] if len(loc) > 0 else None,
            'longitude': loc[1] if len(loc) > 1 else None
        }
    except requests.exceptions.RequestException:
        return {'country': 'Error', 'state': 'Error', 'city': 'Error', 'latitude': None, 'longitude': None}

@st.cache_data
def get_domain_name(ip_address):
    try:
        return socket.gethostbyaddr(ip_address)[0]
    except (socket.herror, TypeError):
        return 'Unknown Domain'

# --- Streamlit User Interface ---
st.title("🌐 IPDR Log Transformation Dashboard")
st.markdown("Upload your IPDR log file, map the columns, and process it to save to the backend database.")

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_file = st.file_uploader("1. Upload your CSV file", type=['csv'])
    st.markdown("2. Map your CSV columns")
    source_ip_col = st.text_input("Source IP Column", value='source_ip')
    destination_ip_col = st.text_input("Destination IP Column", value='destination_ip')
    start_time_col = st.text_input("Session Start Time Column", value='session_start_time')
    end_time_col = st.text_input("Session End Time Column", value='session_end_time')
    data_usage_col_bytes = st.text_input("Data Usage Column (in Bytes)", value='bytes_transferred')

# --- Main Application Logic ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    required_cols = [source_ip_col, destination_ip_col, start_time_col, end_time_col, data_usage_col_bytes]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"Error: The following columns are missing: `{', '.join(missing_cols)}`.")
    else:
        st.dataframe(df.head())
        if st.button("🚀 Process & Save to Database", type="primary"):
            with st.spinner("Processing... This may take a while."):
                st.info("Step 1/6: Assigning user numbers...")
                unique_a_parties = df[source_ip_col].unique()
                ip_to_user_map = {ip: f"user{i+1}" for i, ip in enumerate(unique_a_parties)}
                df['user_number'] = df[source_ip_col].map(ip_to_user_map)

                st.info("Step 2/6: Enriching source IPs with geolocation data...")
                ip_details_cache = {ip: get_ip_details(ip) for ip in unique_a_parties}
                df['country'] = df[source_ip_col].map(lambda ip: ip_details_cache.get(ip, {}).get('country'))
                df['state'] = df[source_ip_col].map(lambda ip: ip_details_cache.get(ip, {}).get('state'))
                df['city'] = df[source_ip_col].map(lambda ip: ip_details_cache.get(ip, {}).get('city'))
                df['latitude'] = df[source_ip_col].map(lambda ip: ip_details_cache.get(ip, {}).get('latitude'))
                df['longitude'] = df[source_ip_col].map(lambda ip: ip_details_cache.get(ip, {}).get('longitude'))

                st.info("Step 3/6: Looking up destination domains...")
                unique_b_parties = df[destination_ip_col].dropna().unique()
                domain_cache = {ip: get_domain_name(ip) for ip in unique_b_parties}
                df['destination_domain'] = df[destination_ip_col].map(domain_cache)

                st.info("Step 4/6: Calculating session durations...")
                df[start_time_col] = pd.to_datetime(df[start_time_col], errors='coerce')
                df[end_time_col] = pd.to_datetime(df[end_time_col], errors='coerce')
                df['total_duration_seconds'] = (df[end_time_col] - df[start_time_col]).dt.total_seconds()
                df = df.drop(columns=[end_time_col])

                st.info("Step 5/6: Converting data usage from Bytes to Megabytes...")
                df[data_usage_col_bytes] = pd.to_numeric(df[data_usage_col_bytes], errors='coerce')
                df['data_usage_mb'] = df[data_usage_col_bytes] / (1024 * 1024)

                st.info("Step 6/6: Finalizing data for database...")
                final_df = df.rename(columns={
                    source_ip_col: 'source_ip',
                    destination_ip_col: 'destination_ip',
                    start_time_col: 'session_start_time'
                })
                
                final_cols_to_keep = [
                    'user_number', 'source_ip', 'country', 'state', 'city', 'latitude', 'longitude',
                    'destination_ip', 'destination_domain', 'session_start_time',
                    'total_duration_seconds', 'data_usage_mb'
                ]
                
                # Filter to keep only the necessary columns, ignoring others
                final_df = final_df[[col for col in final_cols_to_keep if col in final_df.columns]]

            st.success("✅ Transformation Complete!")
            st.dataframe(final_df.head())

            try:
                with st.spinner("Saving data to the backend database..."):
                    final_df.to_sql('ipdr_logs', con=db_engine, if_exists='append', index=False)
                st.success("Data successfully saved! Navigate to the 'Search Data' page to query it.")
            except Exception as e:
                st.error(f"Failed to save data to the database: {e}")