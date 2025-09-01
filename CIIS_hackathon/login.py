import streamlit as st
import sqlite3
import hashlib

# --- Database Setup for Users ---
# Connect to the SQLite database. It will be created if it doesn't exist.
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create the users table if it's not already there
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
''')
conn.commit()

# --- Password Hashing ---
def make_hashes(password):
    """Hashes a password using SHA256."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """Checks if a password matches its hashed version."""
    if make_hashes(password) == hashed_text:
        return True
    return False

# --- Page Configuration ---
st.set_page_config(page_title="Login System", page_icon="🔐", layout="centered")

# --- Initialize Session State ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''

# --- Login / Signup UI ---
st.title("Welcome to the IPDR Analytics Dashboard")

# If user is not authenticated, show the login/signup form
if not st.session_state['authenticated']:
    choice = st.selectbox("Login / Signup", ["Login", "Sign Up"])

    if choice == "Login":
        st.subheader("Login to your account")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')

        if st.button("Login"):
            c.execute('SELECT password FROM users WHERE username =?', (username,))
            data = c.fetchone()
            if data:
                hashed_password_db = data[0]
                if check_hashes(password, hashed_password_db):
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = username
                    st.success(f"Logged in as {username}")
                    st.rerun() # Rerun the script to reflect the new state
                else:
                    st.error("Incorrect username or password")
            else:
                st.error("Incorrect username or password")

    else: # Sign Up
        st.subheader("Create a new account")
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type='password')

        if st.button("Sign Up"):
            try:
                c.execute('INSERT INTO users(username, password) VALUES (?,?)', (new_username, make_hashes(new_password)))
                conn.commit()
                st.success("You have successfully created an account!")
                st.info("Go to the Login menu to login.")
            except sqlite3.IntegrityError:
                st.error("Username already exists. Please choose another one.")
else:
    # --- Main App Logic After Login ---
    st.success(f"Welcome, {st.session_state['username']}!")
    st.markdown("Select a page from the sidebar to begin.")
    
    # This automatically shows the sidebar with pages
    st.sidebar.success("You are logged in.")
    
    if st.button("Logout"):
        st.session_state['authenticated'] = False
        st.session_state['username'] = ''
        st.rerun()

# --- Hide the sidebar pages if not authenticated ---
if not st.session_state['authenticated']:
    # Use CSS to hide the sidebar pages. A bit of a hack but effective.
    st.markdown(
        """
        <style>
            /* This targets the sidebar navigation links */
            div[data-testid="stSidebarNav"] > ul {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True
    )






    
