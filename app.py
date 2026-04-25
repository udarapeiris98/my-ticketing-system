import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, date, timedelta
import time
import plotly.express as px
import io

# --- 1. SUPABASE CONNECTION ---
# ඔබගේ Supabase Settings -> API වෙතින් ලැබුණු URL සහ Key මෙහි ඇතුළත් කරන්න
URL = "https://tfyulwcbjnmrecrukzsm.supabase.co/rest/v1/" 
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRmeXVsd2Niam5tcmVjcnVrenNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcwODQwNTksImV4cCI6MjA5MjY2MDA1OX0.5P22_9CzrKKrMmrn0Vils-gnUlk-jQqzfXAf2M8ulD8"
supabase = create_client(URL, KEY)

# --- 2. DATA FUNCTIONS ---
def get_data():
    try:
        response = supabase.table("tickets").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching tickets: {e}")
        return pd.DataFrame()

def get_users():
    try:
        response = supabase.table("users").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return pd.DataFrame()

# --- 3. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type='password')
    if st.button("Login"):
        try:
            # Supabase හරහා පරිශීලකයා පරීක්ෂා කිරීම
            res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
            if len(res.data) > 0:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = u
                st.rerun()
            else:
                st.error("Invalid Username or Password!")
        except Exception as e:
            st.error(f"Login Error: {e}")
    st.stop()

# --- 4. SIDEBAR NAVIGATION ---
st.sidebar.title(f"👤 {st.session_state['current_user']}")
menu = ["📊 Dashboard", "📅 Schedule View", "🔍 View & Search", "➕ Create Ticket", "🔄 Update & Delete", "📈 Reports", "⚙️ Settings"]
choice = st.sidebar.selectbox("Menu", menu)

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- 5. DASHBOARD ---
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
            .stMetric { background-color: #ffffff !important; padding: 15px !important; border-radius: 12px !important;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important; border: 1px solid #e0e0e0 !important; text-align: center; }
            [data-testid="stMetricValue"] { color: #1a1a1a !important; font-size: 26px !important; font-weight: bold !important; }
            [data-testid="stMetricLabel"] { color: #444444 !important; font-size: 14px !important; }
            </style>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Tickets", total)
        with m2: st.markdown('<div style="border-top: 5px solid #ff4b4b; padding-top:5px;">', unsafe_allow_html=True); st.metric("🔴 Open", open_t); st.markdown('</div>', unsafe_allow_html=True)
        with m3: st.markdown('<div style="border-top: 5px solid #ffa500; padding-top:5px;">', unsafe_allow_html=True); st.metric("🟠 In Progress", prog_t); st.markdown('</div>', unsafe_allow_html=True)
        with m4: st.markdown('<div style="border-top: 5px solid #f1c40f; padding-top:5px;">', unsafe_allow_html=True); st.metric("🟡 Pending", pend_t); st.markdown('</div>', unsafe_allow_html=True)
        with m5: st.markdown('<div style="border-top: 5px solid #28a745; padding-top:5px;">', unsafe_allow_html=True); st.metric("🟢 Completed", comp_t); st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(df, names='status', title="Status Breakdown", hole=0.5), use_container_width=True)
        with c2: st.plotly_chart(px.bar(df, x='priority', color='status', title="Priority Analysis", barmode='group'), use_container_width=True)
    else:
        st.info("No records available.")

# --- 6. SCHEDULE VIEW ---
elif choice == "📅 Schedule View":
    st.title("📅 Ticket Deadlines")
    df = get_data()
    if not df.empty:
        st.dataframe(df[['ticket_number', 'summary', 'due_on', 'assigned_to', 'status']], use_container_width=True)
    else: st.warning("No records found")

# --- 7. VIEW & SEARCH ---
elif choice == "🔍 View & Search":
    st.title("🔍 Advanced Ticket Search")
    df = get_data()
    if not df.empty:
        with st.expander("🎯 Filter Options", expanded=True):
            f1, f2, f3 = st.columns(3)
            sel_status = f1.selectbox("Status", ["All"] + sorted(df['status'].unique().tolist()))
            sel_prio = f2.selectbox("Priority", ["All"] + sorted(df['priority'].unique().tolist()))
            sel_tech = f3.selectbox("Assign To", ["All"] + sorted(df['assigned_to'].unique().tolist()))
            search_query = st.text_input("Filter by Summary/Description")

        filtered_df = df.copy()
        if sel_status != "All": filtered_df = filtered_df[filtered_df['status'] == sel_status]
        if sel_prio != "All": filtered_df = filtered_df[filtered_df['priority'] == sel_prio]
        if sel_tech != "All": filtered_df = filtered_df[filtered_df['assigned_to'] == sel_tech]
        if search_query:
            filtered_df = filtered_df[filtered_df['summary'].str.contains(search_query, case=False, na=False) | filtered_df['description'].str.contains(search_query, case=False, na=False)]

        st.write(f"Showing **{len(filtered_df)}** results")
        st.dataframe(filtered_df.style.set_properties(**{'background-color': '#f9f9f9', 'color': 'black'}), use_container_width=True)
        
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download filtered data as CSV", csv, "filtered_tickets.csv", "text/csv")
    else: st.info("No data found.")

# --- 8. CREATE TICKET ---
elif choice == "➕ Create Ticket":
    st.title("➕ Create New Ticket")
    if 'f_key' not in st.session_state: st.session_state.f_key = 0
    with st.form(key=f"ticket_form_{st.session_state.f_key}"):
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
                ticket_data = {
                    "summary": summ, "description": desc, "assigned_to": assigned, "category": cat,
                    "closed_on": "", "created_on": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "created_by": st.session_state['current_user'], "due_on": str(due),
                    "priority": prio, "organization_name": org, "status": "Open",
                    "time_spent_min": "0", "time_to_resolve": "", "remarks": ""
                }
                try:
                    supabase.table("tickets").insert(ticket_data).execute()
                    st.success("✅ Ticket submitted to Cloud Database!"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Error: {e}")

# --- 9. UPDATE & DELETE ---
elif choice == "🔄 Update & Delete":
    st.title("🔄 Update or Delete Ticket")
    df = get_data()
    if not df.empty:
        ticket_options = {f"{row['ticket_number']} - {row['summary']}": row['ticket_number'] for _, row in df.iterrows()}
        selected_option = st.selectbox("Select Ticket", list(ticket_options.keys()))
        t_id = ticket_options[selected_option]
        row = df[df['ticket_number'] == t_id].iloc[0]
        
        with st.form("update_form"):
            col1, col2 = st.columns(2)
            u_status = col1.selectbox("Status", ["Open", "In Progress", "Pending", "Resolved", "Closed"], index=["Open", "In Progress", "Pending", "Resolved", "Closed"].index(row['status']))
            u_assign = col1.selectbox("Re-assign To", ["Udara", "Supun", "Madushan", "Technician"], index=["Udara", "Supun", "Madushan", "Technician"].index(row['assigned_to']) if row['assigned_to'] in ["Udara", "Supun", "Madushan", "Technician"] else 0)
            u_prio = col2.selectbox("Change Priority", ["Low", "Medium", "High", "Urgent"], index=["Low", "Medium", "High", "Urgent"].index(row['priority']))
            
            try:
                db_date = row.get('due_on')
                current_due_date = pd.to_datetime(db_date).date() if db_date and not pd.isna(db_date) else date.today()
            except: current_due_date = date.today()
                
            u_due_date = col2.date_input("Update Due Date", value=current_due_date)
            u_remarks = st.text_area("Resolution Remarks", value=str(row['remarks'] if row['remarks'] else ""))
            
            if st.form_submit_button("✅ Save Changes"):
                now = datetime.now()
                c_on = row['closed_on']; r_t = row['time_to_resolve']; t_s = row['time_spent_min']
                if u_status in ["Resolved", "Closed"] and not c_on:
                    c_on = now.strftime("%Y-%m-%d %H:%M")
                    try:
                        start = datetime.strptime(row['created_on'], "%Y-%m-%d %H:%M")
                        diff = now - start
                        sec = int(diff.total_seconds())
                        r_t = f"{sec//86400}d {(sec%86400)//3600}h {(sec%3600)//60}m"
                        t_s = str(sec // 60)
                    except: r_t = "N/A"

                upd = {"status": u_status, "assigned_to": u_assign, "priority": u_prio, "due_on": str(u_due_date), "time_spent_min": t_s, "closed_on": c_on, "time_to_resolve": r_t, "remarks": u_remarks}
                supabase.table("tickets").update(upd).eq("ticket_number", t_id).execute()
                st.success("Updated!"); time.sleep(1); st.rerun()

        st.subheader("⚠️ Danger Zone")
        if st.button("🗑️ Delete Ticket permanently") and st.checkbox("Confirm Deletion"):
            supabase.table("tickets").delete().eq("ticket_number", t_id).execute()
            st.warning("Deleted!"); time.sleep(1); st.rerun()

# --- 10. REPORTS ---
elif choice == "📈 Reports":
    st.title("📈 Reports")
    df = get_data()
    if not df.empty:
        df['created_on_dt'] = pd.to_datetime(df['created_on']).dt.date
        s_date = st.date_input("Start", df['created_on_dt'].min())
        e_date = st.date_input("End", df['created_on_dt'].max())
        rep_df = df[(df['created_on_dt'] >= s_date) & (df['created_on_dt'] <= e_date)]
        
        st.write(f"Total: {len(rep_df)}")
        st.dataframe(rep_df, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            rep_df.to_excel(writer, index=False)
        st.download_button("📥 Excel Download", output.getvalue(), "report.xlsx")
    else: st.info("No data.")

# --- 11. SETTINGS ---
elif choice == "⚙️ Settings":
    st.title("⚙️ System Settings")
    st.subheader("🔑 Change Password")
    with st.form("pass_form"):
        new_p = st.text_input("New Password", type="password")
        if st.form_submit_button("Update Password") and new_p:
            supabase.table("users").update({"password": new_p}).eq("username", st.session_state['current_user']).execute()
            st.success("Changed!")

    st.subheader("👤 Create New User")
    with st.form("u_form"):
        new_u = st.text_input("New Username")
        new_up = st.text_input("New Password", type="password")
        if st.form_submit_button("Create") and new_u and new_up:
            try:
                supabase.table("users").insert({"username": new_u, "password": new_up}).execute()
                st.success(f"User {new_u} Created!")
            except: st.error("User exists!")
