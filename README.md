# CIIS-hackathon
 IPDR log analysis and anomaly detection project
 Of course. Here is a comprehensive description for the IPDR log analysis and anomaly detection project we have built.

---

### **Project Title: Intelligent IPDR Log Analysis and Anomaly Detection Dashboard**

#### **Introduction**

This project is a secure, multi-page web application designed for the comprehensive analysis of IP Data Records (IPDR). It provides a full suite of tools for network administrators, security analysts, and data scientists to ingest raw log data, enrich it with valuable context, perform deep-dive analysis, and automatically detect anomalous behavior using machine learning. Built with Python and the Streamlit framework, the application transforms complex log files into an interactive, visual, and actionable intelligence dashboard.

#### **Key Features**

* **Secure User Authentication:** A robust login and signup system ensures that only authorized users can access the application and its sensitive data. Passwords are securely hashed before being stored.
* **Intuitive Data Ingestion:** A user-friendly drag-and-drop interface allows for the easy upload of IPDR logs in CSV format. The system is flexible, enabling users to map column names from their specific file format to the application's processing logic.
* **Automated Data Enrichment:** The application automatically enriches the raw log data by:
    * **Geolocating** source IP addresses to identify their country, state, and city.
    * Performing **reverse DNS lookups** on destination IPs to resolve them into human-readable domain names.
    * Calculating key metrics like **session duration** and converting **data volume** from bytes to megabytes.
* **Centralized Database Storage:** Processed and enriched data is stored in a centralized SQLite database, creating a persistent and queryable backend for all analytical tasks.
* **Interactive Analytics Dashboard:** A powerful search and visualization page allows users to:
    * Filter the entire dataset by user ID, IP addresses (source/destination), destination domain, and custom date ranges.
    * View Key Performance Indicators (KPIs) like total sessions and unique users.
    * Analyze data through interactive charts, including top websites by visits, time spent, and data usage.
    * Visualize the geographic distribution of user activity on a world map.
* **Machine Learning-Powered Anomaly Detection:** The application integrates a `scikit-learn` Isolation Forest model to automatically scan the entire dataset for unusual patterns and outliers, helping to identify potential security threats or network issues.
* **Privacy-Focused Data Management:** A dedicated management page allows users to view all uploaded file records and permanently delete data associated with a specific file, ensuring compliance with privacy requirements.

#### **Technological Stack**

* **Core Language:** Python
* **Web Framework:** Streamlit
* **Data Manipulation & Analysis:** Pandas, NumPy
* **Database:** SQLite (with SQLAlchemy for ORM)
* **Data Visualization:** Plotly, Matplotlib
* **Machine Learning:** Scikit-learn
* **External API Integration:** Requests (for ipinfo.io)

#### **Project Workflow**

1.  **Authentication:** A user begins by either signing up for a new account or logging in through the secure entry page.
2.  **Upload & Process:** The user navigates to the "Upload Data" page, uploads a raw IPDR log file (CSV), and maps the relevant columns. Upon processing, the application enriches the data and saves it to the central SQLite database.
3.  **Analyze & Visualize:** On the "Search Data" page, the user can query the entire database using multiple filters. The results are displayed in both a raw data table and a series of interactive charts and maps.
4.  **Detect Anomalies:** The user can proceed to the "Detect Anomalies" page, where they can run a machine learning model on the dataset to flag suspicious records that deviate from normal patterns.
5.  **Manage Data:** Finally, the user can visit the "Manage Data" page to view a list of all files they've processed and delete specific datasets as needed.

This end-to-end workflow provides a seamless experience, taking a user from raw data to deep, actionable insights within a single, unified platform.
