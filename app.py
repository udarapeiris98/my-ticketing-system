import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import plotly.express as px
import io
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Star Packaging - Ticketing System",
    page_icon="🎫",
    layout="centered"
)

# නිවැරදි ක්‍රමය:
SUPABASE_URL = st.secrets["https://emqwhmimrajxhioiumab.supabase.co/rest/v1/"]
SUPABASE_KEY = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtcXdobWltcmFqeGhpb2l1bWFiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzczNDY5NjYsImV4cCI6MjA5MjkyMjk2Nn0.hoHCuJCk7lwHUMjn4dnJg5Wyj_gZ5tb0aWt5glmGbUk"]
@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type='password')
    if st.button("Login"):
        # Supabase හරහා User පරීක්ෂා කිරීම
        response = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
        if response.data:
            st.session_state['logged_in'] = True
            st.session_state['current_user'] = u
            st.rerun()
        else:
            st.error("Invalid Username or Password!")
    st.stop()

def get_data():
    # Supabase හරහා සියලුම ටිකට් ලබා ගැනීම
    response = supabase.table("tickets").select("*").order("ticket_number", desc=True).execute()
    return pd.DataFrame(response.data)

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title(f"👤 {st.session_state['current_user']}")

# Admin ට පමණක් සියලුම Menu පෙන්වීම
if st.session_state['current_user'] == 'admin':
    menu = ["📊 Dashboard", "📅 Schedule View", "🔍 View & Search", "➕ Create Ticket", "🔄 Update & Delete", "📈 Reports", "⚙️ Settings"]
else:
    # සාමාන්‍ය User ට පෙනෙන්නේ මේවා පමණි
    menu = ["➕ Create Ticket", "🔄 Update & Delete"]

choice = st.sidebar.selectbox("Menu", menu)

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- 4. DASHBOARD (Admin Only) ---
if choice == "📊 Dashboard":
    st.title("📊 Operational Insights")
    df = get_data()
    
    if not df.empty:
        total = len(df)
        open_t = len(df[df['status'] == 'Open'])
        prog_t = len(df[df['status'] == 'In Progress'])
        pend_t = len(df[df['status'] == 'Pending'])
        comp_t = len(df[df['status'].isin(['Resolved', 'Closed'])])

        st.markdown("""
            <style>
            .stMetric {
                background-color: #ffffff !important;
                padding: 15px !important;
                border-radius: 12px !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
                border: 1px solid #e0e0e0 !important;
                text-align: center;
            }
            </style>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total", total)
        m2.metric("🔴 Open", open_t)
        m3.metric("🟠 Progress", prog_t)
        m4.metric("🟡 Pending", pend_t)
        m5.metric("🟢 Closed", comp_t)

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(df, names='status', title="Status Breakdown", hole=0.5), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(df, x='priority', color='status', title="Priority Analysis"), use_container_width=True)
    else:
        st.info("No records available.")

# --- 5. SCHEDULE VIEW ---
elif choice == "📅 Schedule View":
    st.title("📅 Ticket Deadlines")
    df = get_data()
    if not df.empty:
        st.dataframe(df[['ticket_number', 'summary', 'due_on', 'assigned_to', 'status']], use_container_width=True)
    else: st.warning("No records found")

# --- 6. VIEW & SEARCH ---
elif choice == "🔍 View & Search":
    st.title("🔍 Advanced Ticket Search")
    df = get_data()
    if not df.empty:
        search_query = st.text_input("Filter by Summary/Description")
        filtered_df = df[df['summary'].str.contains(search_query, case=False, na=False)] if search_query else df
        st.dataframe(filtered_df, use_container_width=True)
    else: st.info("No data found.")

# --- 7. CREATE TICKET ---
elif choice == "➕ Create Ticket":
    st.title("➕ Create New Ticket")
    with st.form("ticket_form"):
        col1, col2 = st.columns(2)
        summ = col1.text_input("Summary")
        assigned = col1.selectbox("Assign To", ["Udara", "Supun", "Madushan", "Technician"])
        cat = col1.selectbox("Category", ["PC Hardware", "Software", "Network", "Printer", "Email", "CCTV", "Others"])
        prio = col2.selectbox("Priority", ["Low", "Medium", "High", "Urgent"])
        org = col2.text_input("Organization / Dept")
        due = col2.date_input("Due Date", date.today() + timedelta(days=1))
        desc = st.text_area("Detailed Description")
        
        if st.form_submit_button("Submit"):
            if summ:
                data = {
                    "summary": summ, "description": desc, "assigned_to": assigned,
                    "category": cat, "created_on": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "created_by": st.session_state['current_user'], "due_on": str(due),
                    "priority": prio, "organization_name": org, "status": "Open",
                    "time_spent_min": "0", "remarks": ""
                }
                supabase.table("tickets").insert(data).execute()
                st.success("✅ Ticket submitted to Supabase!"); time.sleep(1); st.rerun()

# --- 8. UPDATE & DELETE ---
elif choice == "🔄 Update & Delete":
    st.title("🔄 Update Ticket Details")
    df = get_data()
    if not df.empty:
        ticket_options = {f"{row['ticket_number']} - {row['summary']}": row['ticket_number'] for _, row in df.iterrows()}
        selected_option = st.selectbox("Select Ticket", list(ticket_options.keys()))
        t_id = ticket_options[selected_option]
        row = df[df['ticket_number'] == t_id].iloc[0]
        
        with st.form("update_form"):
            u_status = st.selectbox("Status", ["Open", "In Progress", "Pending", "Resolved", "Closed"], index=["Open", "In Progress", "Pending", "Resolved", "Closed"].index(row['status']))
            u_remarks = st.text_area("Resolution Remarks", value=str(row['remarks'] if row['remarks'] else ""))
            
            if st.form_submit_button("✅ Save Changes"):
                update_data = {"status": u_status, "remarks": u_remarks}
                if u_status in ["Resolved", "Closed"]:
                    update_data["closed_on"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                supabase.table("tickets").update(update_data).eq("ticket_number", t_id).execute()
                st.success("Updated!"); time.sleep(1); st.rerun()

        # Delete (Admin Only)
        if st.session_state['current_user'] == 'admin':
            if st.button("🗑️ Delete Ticket"):
                supabase.table("tickets").delete().eq("ticket_number", t_id).execute()
                st.warning("Deleted!"); time.sleep(1); st.rerun()

# --- 9. REPORTS (Admin Only) ---
elif choice == "📈 Reports":
    st.title("📈 Performance Reports")
    df = get_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        # Download Excel logic මෙතනට එක් කළ හැක

# --- 10. SETTINGS (Admin Only) ---
elif choice == "⚙️ Settings":
    st.title("⚙️ System Settings")
    # User Creation logic
    with st.form("new_user"):
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password")
        if st.form_submit_button("Create User"):
            supabase.table("users").insert({"username": new_u, "password": new_p}).execute()
            st.success("User Created!")
