import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import plotly.express as px
import io
import time

# --- 1. SUPABASE CONNECTION ---
# මෙතැනට ඔබේ URL සහ Key නිවැරදිව ඇතුළත් කරන්න
url: str = "https://hjttradlagsogfgdyhai.supabase.co/rest/v1/"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhqdHRyYWRsYWdzb2dmZ2R5aGFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3MjU5MDAsImV4cCI6MjA5MjMwMTkwMH0.WcdJpwm_geu5swZ4qrsKYv9kPxQnrvC17ebndCq15xc"
supabase: Client = create_client(url, key)

# --- 2. DATA FUNCTIONS ---
def get_data():
    try:
        # 'SELECT *' මඟින් සියලුම දත්ත ලබා ගැනීම
        response = supabase.table("tickets").select("*").execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

def login_user(u, p):
    response = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
    return len(response.data) > 0

# --- 3. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Secure Login")
    u = st.text_input("username")
    p = st.text_input("password", type='password')
    if st.button("Login"):
        if login_user(u, p):
            st.session_state['logged_in'] = True
            st.session_state['current_user'] = u
            st.rerun()
        else: st.error("Invalid Login!")
    st.stop()

# --- 4. NAVIGATION ---
menu = ["📊 Dashboard", "📅 Schedule View", "🔍 View & Search", "➕ Create Ticket", "🔄 Update & Delete", "📈 Reports", "⚙️ Settings"]
choice = st.sidebar.selectbox("Menu", menu)

# --- 5. DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("📊 Dashboard")
    df = get_data()
    if not df.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", len(df))
        m2.metric("Open", len(df[df['status'] == 'Open']))
        # ප්‍රස්තාර පෙන්වීම
        st.plotly_chart(px.pie(df, names='status', title="Status Breakdown", hole=0.4), use_container_width=True)
    else: st.info("දත්ත නැත.")

# --- 6. SCHEDULE VIEW & SEARCH ---
elif choice == "📅 Schedule View":
    st.title("📅 Schedule View")
    df = get_data()
    if not df.empty:
        # අවශ්‍ය columns පමණක් පෙන්වීම
        st.dataframe(df[['ticket_number', 'summary', 'due_on', 'assigned_to', 'status']], use_container_width=True)

elif choice == "🔍 View & Search":
    st.title("🔍 View & Search")
    df = get_data()
    if not df.empty:
        search = st.text_input("Search ID or Summary")
        if search:
            df = df[df['ticket_number'].astype(str).str.contains(search) | df['summary'].str.contains(search, case=False)]
        st.dataframe(df, use_container_width=True)

# --- 7. CREATE TICKET ---
elif choice == "➕ Create Ticket":
    st.title("➕ Create New Ticket")
    if 'f_key' not in st.session_state: st.session_state.f_key = 0
    with st.form(key=f"t_form_{st.session_state.f_key}"):
        summ = st.text_input("Summary")
        prio = st.selectbox("Priority", ["Low", "Medium", "High", "Urgent"])
        due = st.date_input("Due Date", date.today() + timedelta(days=1))
        assigned = st.selectbox("Assign To", ["Admin", "Supun", "Udara"])
        desc = st.text_area("Description")
        
        if st.form_submit_button("Submit"):
            if summ:
                # 'remarks' ඇතුළුව දත්ත ඇතුළත් කිරීම
                data = {
                    "summary": summ, "description": desc, "assigned_to": assigned,
                    "created_on": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "due_on": str(due), "priority": prio, "status": "Open", "remarks": ""
                }
                supabase.table("tickets").insert(data).execute()
                st.success("Ticket Created!"); time.sleep(1); st.rerun()

# --- 8. UPDATE & DELETE ---
elif choice == "🔄 Update & Delete":
    st.title("🔄 Update or Delete")
    df = get_data()
    if not df.empty:
        t_id = st.selectbox("Select ID", df['ticket_number'].tolist())
        row = df[df['ticket_number'] == t_id].iloc[0]
        
        new_status = st.selectbox("Status", ["Open", "In Progress", "Resolved", "Closed"], 
                                  index=["Open", "In Progress", "Resolved", "Closed"].index(row['status']))
        res_remarks = st.text_area("Remarks", value=str(row['remarks'] if row['remarks'] else ""))
        
        col1, col2 = st.columns(2)
        if col1.button("Update"):
            up_data = {"status": new_status, "remarks": res_remarks}
            if new_status in ["Resolved", "Closed"]:
                now = datetime.now()
                up_data["closed_on"] = now.strftime("%Y-%m-%d %H:%M")
                # කාලය ගණනය කිරීම
                try:
                    start = datetime.strptime(row['created_on'], "%Y-%m-%d %H:%M")
                    diff = now - start
                    sec = int(diff.total_seconds())
                    up_data["time_to_resolve"] = f"{sec//86400}d {(sec%86400)//3600}h {(sec%3600)//60}m"
                    up_data["time_spent_min"] = str(sec // 60)
                except: pass
            supabase.table("tickets").update(up_data).eq("ticket_number", t_id).execute()
            st.success("Updated!"); time.sleep(1); st.rerun()
            
        if col2.button("Delete"):
            supabase.table("tickets").delete().eq("ticket_number", t_id).execute()
            st.warning("Deleted!"); time.sleep(1); st.rerun()

# --- 9. REPORTS ---
elif choice == "📈 Reports":
    st.title("📈 Reports")
    df = get_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("Download Excel", output.getvalue(), "Report.xlsx")
