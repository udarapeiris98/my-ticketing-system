import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import plotly.express as px
import io
import time

# --- 1. DATABASE SETUP ---
DB_NAME = 'ticketing_sys.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
        ticket_number INTEGER PRIMARY KEY AUTOINCREMENT, 
        summary TEXT, description TEXT, assigned_to TEXT, category TEXT, 
        closed_on TEXT, created_on TEXT, created_by TEXT, due_on TEXT, 
        priority TEXT, organization_name TEXT, status TEXT, 
        time_spent_min TEXT, time_to_resolve TEXT, remarks TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES ('admin', '123')")
    conn.commit()
    conn.close()

init_db()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type='password')
    if st.button("Login"):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        if c.fetchone():
            st.session_state['logged_in'] = True
            st.session_state['current_user'] = u
            st.rerun()
        else: st.error("Invalid Username or Password!")
    st.stop()

def get_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM tickets", conn)
    conn.close()
    return df

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title(f"👤 {st.session_state['current_user']}")
menu = ["📊 Dashboard", "📅 Schedule View", "🔍 View & Search", "➕ Create Ticket", "🔄 Update & Delete", "📈 Reports", "⚙️ Settings"]
choice = st.sidebar.selectbox("Menu", menu)

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- 4. DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("📊 Operational Insights")
    df = get_data()
    if not df.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Tickets", len(df))
        m2.metric("Open", len(df[df['status'] == 'Open']))
        m3.metric("In Progress", len(df[df['status'] == 'In Progress']))
        m4.metric("Completed", len(df[df['status'].isin(['Resolved', 'Closed'])]))
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(df, names='status', title="Status Breakdown", hole=0.4), use_container_width=True)
        with c2: st.plotly_chart(px.bar(df, x='priority', color='status', title="Priority Analysis"), use_container_width=True)
    else: st.info("No records found")

# --- 5. SCHEDULE VIEW ---
elif choice == "📅 Schedule View":
    st.title("📅 Ticket Deadlines")
    df = get_data()
    if not df.empty:
        st.dataframe(df[['ticket_number', 'summary', 'due_on', 'assigned_to', 'status']], use_container_width=True)
    else: st.warning("No records found")

# --- 6. VIEW & SEARCH ---
elif choice == "🔍 View & Search":
    st.title("🔍 Search & View All")
    df = get_data()
    if not df.empty:
        search = st.text_input("Search by ID or Summary")
        if search:
            df = df[df['ticket_number'].astype(str).str.contains(search) | df['summary'].str.contains(search, case=False)]
        st.dataframe(df, use_container_width=True)

# --- 7. CREATE TICKET ---
elif choice == "➕ Create Ticket":
    st.title("➕ Create New Ticket")
    if 'f_key' not in st.session_state: st.session_state.f_key = 0
    with st.form(key=f"ticket_form_{st.session_state.f_key}"):
        col1, col2 = st.columns(2)
        summ = col1.text_input("Summary")
        assigned = col1.selectbox("Assign To", ["Admin", "Supun", "Udara", "Technician"])
        cat = col1.selectbox("Category", ["Hardware", "Software", "Network", "Other"])
        prio = col2.selectbox("Priority", ["Low", "Medium", "High", "Urgent"])
        org = col2.text_input("Organization / Dept")
        due = col2.date_input("Due Date", date.today() + timedelta(days=1))
        desc = st.text_area("Detailed Description")
        b1, b2, _ = st.columns([1, 1, 4])
        if b1.form_submit_button("Submit"):
            if summ:
                conn = sqlite3.connect(DB_NAME); c = conn.cursor()
                c.execute('''INSERT INTO tickets (summary, description, assigned_to, category, closed_on, created_on, created_by, due_on, priority, organization_name, status, time_spent_min, time_to_resolve, remarks) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                          (summ, desc, assigned, cat, "", datetime.now().strftime("%Y-%m-%d %H:%M"), 
                           st.session_state['current_user'], str(due), prio, org, "Open", "0", "", ""))
                conn.commit(); conn.close()
                st.success("✅ Ticket submitted successfully!"); time.sleep(1); st.rerun()
        if b2.form_submit_button("Clear"):
            st.session_state.f_key += 1
            st.rerun()

# --- 8. UPDATE & DELETE ---
elif choice == "🔄 Update & Delete":
    st.title("🔄 Update or Delete Ticket")
    df = get_data()
    if not df.empty:
        search_id = st.text_input("Enter Ticket ID to search", "")
        filtered_df = df[df['ticket_number'].astype(str).str.contains(search_id)] if search_id else df
        if not filtered_df.empty:
            t_id = st.selectbox("Pick a Ticket ID to update", filtered_df['ticket_number'].tolist())
            row = df[df['ticket_number'] == t_id].iloc[0]
            new_status = st.selectbox("Update Status", ["Open", "In Progress", "Pending", "Resolved", "Closed"], 
                                      index=["Open", "In Progress", "Pending", "Resolved", "Closed"].index(row['status']))
            res_remarks = st.text_area("Please enter the resolution details.", value=str(row['remarks'] if row['remarks'] else ""))
            col_u, col_d, _ = st.columns([1, 1, 3])
            if col_u.button("Update"):
                closed_on, res_time, t_spent = str(row['closed_on']), str(row['time_to_resolve']), str(row['time_spent_min'])
                if new_status in ["Resolved", "Closed"]:
                    now = datetime.now()
                    closed_on = now.strftime("%Y-%m-%d %H:%M")
                    try:
                        start = datetime.strptime(row['created_on'], "%Y-%m-%d %H:%M")
                        diff = now - start
                        sec = int(diff.total_seconds())
                        res_time = f"{sec//86400}d {(sec%86400)//3600}h {(sec%3600)//60}m"
                        t_spent = str(sec // 60)
                    except: res_time = "N/A"
                conn = sqlite3.connect(DB_NAME); c = conn.cursor()
                c.execute("UPDATE tickets SET status=?, time_spent_min=?, closed_on=?, time_to_resolve=?, remarks=? WHERE ticket_number=?",
                          (new_status, t_spent, closed_on, res_time, res_remarks, t_id))
                conn.commit(); conn.close()
                st.success("🔄 Updated successfully!"); time.sleep(1); st.rerun()
            if col_d.button("🗑️ Delete Ticket"):
                conn = sqlite3.connect(DB_NAME); c = conn.cursor()
                c.execute("DELETE FROM tickets WHERE ticket_number=?", (t_id,))
                conn.commit(); conn.close()
                st.warning("🗑️ Ticket deleted successfully!"); time.sleep(1); st.rerun()
        else: st.warning("No ticket was found.")

# --- 9. REPORTS ---
elif choice == "📈 Reports":
    st.title("📈 Operational Reports")
    df = get_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Excel Download", output.getvalue(), "Ticket_Report.xlsx")

# --- 10. SETTINGS (Admin Password & User Creation) ---
elif choice == "⚙️ Settings":
    st.title("⚙️ System Settings")
    
    # කොටස 1: Change Password
    st.subheader("🔑 Change Password")
    with st.form("change_pass_form"):
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update Password"):
            if new_pass == confirm_pass and new_pass != "":
                conn = sqlite3.connect(DB_NAME); c = conn.cursor()
                c.execute("UPDATE users SET password=? WHERE username=?", (new_pass, st.session_state['current_user']))
                conn.commit(); conn.close()
                st.success("✅ The password has been changed successfully!")
            else:
                st.error("❌ The password does not match or is empty!")

    st.divider()

    # කොටස 2: Create New User
    st.subheader("👤 Create New User")
    with st.form("create_user_form"):
        new_username = st.text_input("New Username")
        new_user_pass = st.text_input("New User Password", type="password")
        if st.form_submit_button("Create User"):
            if new_username != "" and new_user_pass != "":
                try:
                    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
                    c.execute("INSERT INTO users VALUES (?,?)", (new_username, new_user_pass))
                    conn.commit(); conn.close()
                    st.success(f"✅ User '{new_username}' Successfully created!")
                except sqlite3.IntegrityError:
                    st.error("❌ This username already exists in the system!")
            else:
                st.error("❌ Please enter the username and password!")