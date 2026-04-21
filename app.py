import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import plotly.express as px
import io
import time

# --- 1. SUPABASE CONNECTION ---
# ඔබ ලබාගත් URL සහ Key මෙතැනට නිවැරදිව ඇතුළත් කරන්න
url: str = "https://hjttradlagsogfgdyhai.supabase.co/rest/v1/"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhqdHRyYWRsYWdzb2dmZ2R5aGFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3MjU5MDAsImV4cCI6MjA5MjMwMTkwMH0.WcdJpwm_geu5swZ4qrsKYv9kPxQnrvC17ebndCq15xc"

@st.cache_resource
def init_connection():
    return create_client(url, key)

supabase = init_connection()

# --- 2. DATA FUNCTIONS ---
def get_data():
    try:
        # Schema එක public බව සහතික කර දත්ත ලබා ගැනීම
        response = supabase.table("tickets").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching tickets: {e}")
        return pd.DataFrame()

def login_user(u, p):
    try:
        # මෙහිදී .eq() භාවිතයෙන් admin/123 පරීක්ෂා කරයි
        response = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
        return len(response.data) > 0
    except Exception as e:
        # ලොග් වීමේදී ඇතිවන ගැටලුව තිරය මත පෙන්වයි
        st.error(f"Login System Error: {e}")
        return False

# --- 3. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Secure Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type='password')
    if st.button("Login"):
        if login_user(u, p):
            st.session_state['logged_in'] = True
            st.session_state['current_user'] = u
            st.rerun()
        else:
            st.error("වැරදි පරිශීලක නාමයක් හෝ මුරපදයක්!")
    st.stop()

# --- 4. NAVIGATION & OTHER UI ---
# (Dashboard, Create Ticket වැනි අනෙක් කොටස් මෙතැන් සිට කලින් පරිදිම පවතී...)
st.sidebar.success(f"Connected as: {st.session_state['current_user']}")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

st.title("🎟️ IT Ticketing System")
st.write("Welcome to Star Packaging IT Support Portal")
            df.to_excel(writer, index=False)
        st.download_button("Download Excel", output.getvalue(), "Report.xlsx")
