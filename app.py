import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
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

# --- 1. SUPABASE DATABASE CONNECTION ---
# මෙහි 'your_connection_string' වෙනුවට Supabase Settings වල ඇති Connection String එක ලබාදෙන්න.
DB_URL = "postgresql://postgres:[YOUR_PASSWORD]@db.[YOUR_PROJECT_REF].supabase.co:5432/postgres"

engine = create_engine(DB_URL)

def init_db():
    with engine.connect() as conn:
        conn.execute(text('''CREATE TABLE IF NOT EXISTS tickets (
            ticket_number SERIAL PRIMARY KEY, 
            summary TEXT, description TEXT, assigned_to TEXT, category TEXT, 
            closed_on TEXT, created_on TEXT, created_by TEXT, due_on TEXT, 
            priority TEXT, organization_name TEXT, status TEXT, 
            time_spent_min TEXT, time_to_resolve TEXT, remarks TEXT)'''))
        
        conn.execute(text('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)'''))
        
        res = conn.execute(text("SELECT COUNT(*) FROM users")).fetchone()
        if res[0] == 0:
            conn.execute(text("INSERT INTO users (username, password) VALUES ('admin', '123')"))
        conn.commit()

init_db()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type='password')
    if st.button("Login"):
        with engine.connect() as conn:
            res = conn.execute(text("SELECT * FROM users WHERE username=:u AND password=:p"), {"u": u, "p": p}).fetchone()
            if res:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = u
                st.rerun()
            else: st.error("Invalid Username or Password!")
    st.stop()

def get_data():
    return pd.read_sql("SELECT * FROM tickets ORDER BY ticket_number ASC", engine)

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title(f"👤 {st.session_state['current_user']}")

if st.session_state['current_user'] == 'admin':
    menu = ["📊 Dashboard", "📅 Schedule View", "🔍 View & Search", "➕ Create Ticket", "🔄 Update & Delete", "📈 Reports", "⚙️ Settings"]
else:
    menu = ["➕ Create Ticket", "🔄 Update & Delete"]

choice = st.sidebar.selectbox("Menu", menu)

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- 4. DASHBOARD ---
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
        m1.metric(label="Total Tickets", value=total)
        with m2: 
            st.markdown('<div style="border-top: 5px solid #ff4b4b; padding-top:5px;">', unsafe_allow_html=True)
            st.metric(label="🔴 Open", value=open_t)
            st.markdown('</div>', unsafe_allow_html=True)
        with m3:
            st.markdown('<div style="border-top: 5px solid #ffa500; padding-top:5px;">', unsafe_allow_html=True)
            st.metric(label="🟠 In Progress", value=prog_t)
            st.markdown('</div>', unsafe_allow_html=True)
        with m4:
            st.markdown('<div style="border-top: 5px solid #f1c40f; padding-top:5px;">', unsafe_allow_html=True)
            st.metric(label="🟡 Pending", value=pend_t)
            st.markdown('</div>', unsafe_allow_html=True)
        with m5:
            st.markdown('<div style="border-top: 5px solid #28a745; padding-top:5px;">', unsafe_allow_html=True)
            st.metric(label="🟢 Completed", value=comp_t)
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(df, names='status', title="Status Breakdown", hole=0.5), use_container_width=True)
        with c2: st.plotly_chart(px.bar(df, x='priority', color='status', title="Priority Analysis", barmode='group'), use_container_width=True)
    else: st.info("No records available.")

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
        with st.expander("🎯 Filter Options", expanded=True):
            f1, f2, f3 = st.columns(3)
            status_list = ["All"] + sorted(df['status'].unique().tolist())
            sel_status = f1.selectbox("Status", status_list)
            prio_list = ["All"] + sorted(df['priority'].unique().tolist())
            sel_prio = f2.selectbox("Priority", prio_list)
            tech_list = ["All"] + sorted(df['assigned_to'].unique().tolist())
            sel_tech = f3.selectbox("Assign To", tech_list)
            search_query = st.text_input("Filter by Summary/Description")

        filtered_df = df.copy()
        if sel_status != "All": filtered_df = filtered_df[filtered_df['status'] == sel_status]
        if sel_prio != "All": filtered_df = filtered_df[filtered_df['priority'] == sel_prio]
        if sel_tech != "All": filtered_df = filtered_df[filtered_df['assigned_to'] == sel_tech]
        if search_query:
            filtered_df = filtered_df[filtered_df['summary'].str.contains(search_query, case=False, na=False) | 
                                    filtered_df['description'].str.contains(search_query, case=False, na=False)]

        st.write(f"Showing **{len(filtered_df)}** results")
        st.dataframe(filtered_df, use_container_width=True)
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download filtered data as CSV", csv, "filtered_tickets.csv", "text/csv")
    else: st.info("No data found in the system.")

# --- 7. CREATE TICKET ---
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
                with engine.connect() as conn:
                    conn.execute(text('''INSERT INTO tickets (summary, description, assigned_to, category, closed_on, created_on, created_by, due_on, priority, organization_name, status, time_spent_min, time_to_resolve, remarks) 
                                 VALUES (:s,:d,:a,:c,:cl,:cr,:cb,:du,:p,:o,:st,:ts,:tr,:r)'''),
                                 {"s":summ, "d":desc, "a":assigned, "c":cat, "cl":"", "cr":datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                  "cb":st.session_state['current_user'], "du":str(due), "p":prio, "o":org, "st":"Open", "ts":"0", "tr":"", "r":""})
                    conn.commit()
                st.success("✅ Ticket submitted!"); time.sleep(1); st.rerun()

# --- 8. UPDATE & DELETE ---
elif choice == "🔄 Update & Delete":
    st.title("🔄 Update Ticket Details")
    df = get_data()
    if not df.empty:
        ticket_options = {f"{row['ticket_number']} - {row['summary']}": row['ticket_number'] for _, row in df.iterrows()}
        selected_option = st.selectbox("Select Ticket", list(ticket_options.keys()))
        t_id = ticket_options[selected_option]
        row = df[df['ticket_number'] == t_id].iloc[0]
        
        with st.form("update_form_new"):
            col1, col2 = st.columns(2)
            u_status = col1.selectbox("Status", ["Open", "In Progress", "Pending", "Resolved", "Closed"], index=["Open", "In Progress", "Pending", "Resolved", "Closed"].index(row['status']))
            u_assign = col1.selectbox("Re-assign To", ["Udara", "Supun", "Madushan", "Technician"], index=0)
            u_prio = col2.selectbox("Change Priority", ["Low", "Medium", "High", "Urgent"], index=["Low", "Medium", "High", "Urgent"].index(row['priority']))
            u_due_date = col2.date_input("Update Due Date", value=datetime.now().date())
            u_remarks = st.text_area("Resolution Remarks", value=str(row['remarks'] if row['remarks'] else ""))
            
            if st.form_submit_button("✅ Update"):
                closed_on, res_time, t_spent = str(row['closed_on']), str(row['time_to_resolve']), str(row['time_spent_min'])
                if u_status in ["Resolved", "Closed"] and (not row['closed_on'] or row['closed_on'] == ""):
                    now = datetime.now()
                    closed_on = now.strftime("%Y-%m-%d %H:%M")
                    try:
                        start = datetime.strptime(row['created_on'], "%Y-%m-%d %H:%M")
                        diff = now - start
                        sec = int(diff.total_seconds())
                        res_time = f"{sec//86400}d {(sec%86400)//3600}h {(sec%3600)//60}m"
                        t_spent = str(sec // 60)
                    except: res_time = "N/A"
                
                with engine.connect() as conn:
                    conn.execute(text("""UPDATE tickets SET status=:st, assigned_to=:a, priority=:p, due_on=:d, time_spent_min=:ts, closed_on=:cl, time_to_resolve=:tr, remarks=:r WHERE ticket_number=:id"""),
                                 {"st":u_status, "a":u_assign, "p":u_prio, "d":str(u_due_date), "ts":t_spent, "cl":closed_on, "tr":res_time, "r":u_remarks, "id":t_id})
                    conn.commit()
                st.toast(f"Ticket {t_id} updated!", icon='✅'); time.sleep(1); st.rerun()

        if st.session_state['current_user'] == 'admin':
            st.subheader("⚠️ Admin: Delete Ticket")
            if st.button("🗑️ Delete Ticket permanently"):
                with engine.connect() as conn:
                    conn.execute(text("DELETE FROM tickets WHERE ticket_number=:id"), {"id": t_id})
                    conn.commit()
                st.warning(f"Ticket {t_id} removed."); time.sleep(1); st.rerun()
    else: st.info("No tickets to update.")

# --- 9. REPORTS (ADMIN ONLY) ---
elif choice == "📈 Reports":
    st.title("📈 Operational Performance Reports")
    df = get_data()
    if not df.empty:
        df['created_on_dt'] = pd.to_datetime(df['created_on']).dt.date
        col_f1, col_f2 = st.columns(2)
        start_date = col_f1.date_input("Start Date", df['created_on_dt'].min())
        end_date = col_f2.date_input("End Date", df['created_on_dt'].max())
        report_df = df.loc[(df['created_on_dt'] >= start_date) & (df['created_on_dt'] <= end_date)]

        st.subheader("📋 Summary")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Total Tickets", len(report_df))
        r2.metric("Total Resolved", len(report_df[report_df['status'].isin(['Resolved', 'Closed'])]))
        avg_time = pd.to_numeric(report_df['time_spent_min'], errors='coerce').mean()
        r3.metric("Average Time", f"{avg_time:.1f} Min" if not pd.isna(avg_time) else "N/A")
        top_cat = report_df['category'].mode()[0] if not report_df['category'].empty else "N/A"
        r4.metric("Main Issue", top_cat)

        col_c1, col_c2 = st.columns(2)
        with col_c1: st.plotly_chart(px.bar(report_df, x='assigned_to', color='status', title="Technician Performance"), use_container_width=True)
        with col_c2: st.plotly_chart(px.histogram(report_df, x='category', title="Issue Categorization"), use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            report_df.to_excel(writer, index=False, sheet_name='Ticket Report')
        st.download_button(label="📥 Download Excel", data=output.getvalue(), file_name=f"Report_{start_date}.xlsx")
    else: st.info("No records available.")

# --- 10. SETTINGS (ADMIN ONLY) ---
elif choice == "⚙️ Settings":
    st.title("⚙️ System Settings")
    st.subheader("🔑 Change Password")
    with st.form("change_pass_form"):
        new_pass = st.text_input("New Password", type="password")
        if st.form_submit_button("Update Password"):
            if new_pass != "":
                with engine.connect() as conn:
                    conn.execute(text("UPDATE users SET password=:p WHERE username=:u"), {"p":new_pass, "u":st.session_state['current_user']})
                    conn.commit()
                st.success("✅ Password updated!")

    st.divider()
    st.subheader("👤 Create New User")
    with st.form("create_user_form"):
        new_username = st.text_input("New Username")
        new_user_pass = st.text_input("New User Password", type="password")
        if st.form_submit_button("Create User"):
            if new_username and new_user_pass:
                try:
                    with engine.connect() as conn:
                        conn.execute(text("INSERT INTO users (username, password) VALUES (:u, :p)"), {"u":new_username, "p":new_user_pass})
                        conn.commit()
                    st.success(f"✅ User '{new_username}' created!")
                except: st.error("❌ Error or Username exists!")
