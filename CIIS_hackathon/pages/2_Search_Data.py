import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import datetime
import plotly.express as px

import streamlit as st

# --- Authentication Check ---
if not st.session_state.get('authenticated', False):
    st.error("You must be logged in to view this page.")
    st.stop()


# --- Page Configuration ---
st.set_page_config(page_title="IPDR Data Analytics", page_icon="📊", layout="wide")

# --- Database Connection ---
try:
    db_engine = create_engine('sqlite:///ipdr_data.db')
except Exception as e:
    st.error(f"Could not connect to the database: {e}")
    st.stop()

# --- Main Search Interface ---
st.title("📊 IPDR Data Analytics Dashboard")
st.markdown("Use the filters below to query the logs and visualize the results.")

# --- UI for Search and Filters ---
with st.expander("Show Search Filters", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        user_search = st.text_input("Search by User Number")
        source_ip_search = st.text_input("Search by Source IP")
    with col2:
        domain_search = st.text_input("Search by Destination Domain")
        dest_ip_search = st.text_input("Search by Destination IP")

    st.markdown("##### Filter by Session Start Time")
    try:
        min_date_db = pd.read_sql("SELECT MIN(session_start_time) FROM ipdr_logs", db_engine).iloc[0, 0]
        max_date_db = pd.read_sql("SELECT MAX(session_start_time) FROM ipdr_logs", db_engine).iloc[0, 0]
        min_date = pd.to_datetime(min_date_db).date() if min_date_db else datetime.date.today() - datetime.timedelta(days=30)
        max_date = pd.to_datetime(max_date_db).date() if max_date_db else datetime.date.today()
    except Exception:
        st.info("No data in the database yet. Upload a file on the main page.")
        st.stop()

    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
    with date_col2:
        end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

# --- Session State to hold search results ---
if 'results_df' not in st.session_state:
    st.session_state.results_df = pd.DataFrame()

# --- Build and Execute the Query ---
if st.button("Search & Analyze", type="primary"):
    query = "SELECT * FROM ipdr_logs WHERE 1=1"
    params = {}
    if user_search: query += " AND user_number LIKE :user"; params['user'] = f"%{user_search}%"
    if domain_search: query += " AND destination_domain LIKE :domain"; params['domain'] = f"%{domain_search}%"
    if source_ip_search: query += " AND source_ip LIKE :source_ip"; params['source_ip'] = f"%{source_ip_search}%"
    if dest_ip_search: query += " AND destination_ip LIKE :dest_ip"; params['dest_ip'] = f"%{dest_ip_search}%"
    if start_date and end_date:
        query += " AND session_start_time BETWEEN :start AND :end"
        params['start'] = str(start_date)
        params['end'] = str(end_date + datetime.timedelta(days=1))

    with st.spinner("Searching the database..."):
        try:
            st.session_state.results_df = pd.read_sql(query, db_engine, params=params)
        except Exception as e:
            st.error(f"An error occurred while querying the database: {e}")
            st.session_state.results_df = pd.DataFrame()

# --- Display Results and Visualizations ---
if not st.session_state.results_df.empty:
    df = st.session_state.results_df
    st.markdown("---")
    st.header("📈 Analytics Dashboard")
    st.write(f"Displaying analytics for **{len(df)}** records found.")

    total_sessions = len(df)
    unique_users = df['user_number'].nunique()
    total_duration_hours = df['total_duration_seconds'].sum() / 3600
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Sessions", f"{total_sessions:,}")
    kpi2.metric("Unique Users", f"{unique_users:,}")
    kpi3.metric("Total Duration (Hours)", f"{total_duration_hours:,.2f}")
    st.markdown("---")

    viz_col1, viz_col2 = st.columns(2)
    with viz_col1:
        st.subheader("Top 10 Websites by Visits")
        top_domains_visits = df['destination_domain'].value_counts().nlargest(10)
        fig_pie = px.pie(top_domains_visits, values=top_domains_visits.values, names=top_domains_visits.index)
        st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("Top 10 Sites by Data Usage (MB)")
        if 'data_usage_mb' in df.columns:
            data_usage = df.groupby('destination_domain')['data_usage_mb'].sum().nlargest(10)
            fig_bar_data = px.bar(data_usage, x=data_usage.index, y=data_usage.values, labels={'y': 'Total Data Usage (MB)', 'x': 'Website Domain'})
            st.plotly_chart(fig_bar_data, use_container_width=True)
        else:
            st.warning("Data Usage column ('data_usage_mb') not found in database.")

    with viz_col2:
        st.subheader("Top 10 Websites by Time Spent")
        time_spent = df.groupby('destination_domain')['total_duration_seconds'].sum().div(60).nlargest(10)
        fig_bar_time = px.bar(time_spent, y=time_spent.index, x=time_spent.values, orientation='h', labels={'x': 'Total Duration (Minutes)', 'y': 'Website Domain'})
        fig_bar_time.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar_time, use_container_width=True)

    st.subheader("Geographic Distribution of User Sessions")
    map_df = df.dropna(subset=['latitude', 'longitude'])
    if not map_df.empty:
        map_df['latitude'] = pd.to_numeric(map_df['latitude'], errors='coerce')
        map_df['longitude'] = pd.to_numeric(map_df['longitude'], errors='coerce')
        st.map(map_df.dropna(subset=['latitude', 'longitude']))
    else:
        st.warning("No valid location data available to display on the map.")

    with st.expander("Show Raw Search Results"):
        st.dataframe(df)

elif st.session_state.get('results_df') is not None:
    st.info("No records found matching your criteria. Please adjust your filters.")

