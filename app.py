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
        # Calculate data
        total = len(df)
        open_t = len(df[df['status'] == 'Open'])
        prog_t = len(df[df['status'] == 'In Progress'])
        pend_t = len(df[df['status'] == 'Pending'])
        comp_t = len(df[df['status'].isin(['Resolved', 'Closed'])])

        # Style card (CSS)
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
            [data-testid="stMetricValue"] {
                color: #1a1a1a !important;
                font-size: 26px !important;
                font-weight: bold !important;
            }
            [data-testid="stMetricLabel"] {
                color: #444444 !important;
                font-size: 14px !important;
            }
            </style>
        """, unsafe_allow_html=True)

        
        m1, m2, m3, m4, m5 = st.columns(5)
        
        with m1:
            st.metric(label="Total Tickets", value=total)
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

        #
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(df, names='status', title="Status Breakdown", hole=0.5)
            st.plotly_chart(fig_pie, use_container_width=True, key="dashboard_pie_chart")
            
        with c2:
            fig_bar = px.bar(df, x='priority', color='status', title="Priority Analysis", barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True, key="dashboard_bar_chart")

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
        # --- FILTER INTERFACE ---
        with st.expander("🎯 Filter Options", expanded=True):
            f1, f2, f3 = st.columns(3)
            
            # 1. Status Filter
            status_list = ["All"] + sorted(df['status'].unique().tolist())
            sel_status = f1.selectbox("Status", status_list)
            
            # 2. Priority Filter
            prio_list = ["All"] + sorted(df['priority'].unique().tolist())
            sel_prio = f2.selectbox("Priority", prio_list)
            
            # 3. Technician Filter (Assigned To)
            tech_list = ["All"] + sorted(df['assigned_to'].unique().tolist())
            sel_tech = f3.selectbox("Assign To", tech_list)

            # 4. Keyword Search
            search_query = st.text_input("Filter by Summary/Description")

        # --- DATA FILTERING LOGIC ---
        filtered_df = df.copy()
        
        if sel_status != "All":
            filtered_df = filtered_df[filtered_df['status'] == sel_status]
        
        if sel_prio != "All":
            filtered_df = filtered_df[filtered_df['priority'] == sel_prio]
            
        if sel_tech != "All":
            filtered_df = filtered_df[filtered_df['assigned_to'] == sel_tech]
            
        if search_query:
            filtered_df = filtered_df[
                filtered_df['summary'].str.contains(search_query, case=False, na=False) | 
                filtered_df['description'].str.contains(search_query, case=False, na=False)
            ]

        # --- RESULTS DISPLAY ---
        st.write(f"Showing **{len(filtered_df)}** results")
        

        st.dataframe(
            filtered_df.style.set_properties(**{'background-color': '#f9f9f9', 'color': 'black'}),
            use_container_width=True
        )

        # Download Button 
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download filtered data as CSV", csv, "filtered_tickets.csv", "text/csv")

    else:
        st.info("No data found in the system.")

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
# --- UPDATE TICKET SECTION (WITH DUE DATE) ---
# --- UPDATE TICKET SECTION (FIXED FOR NaTType & SUBMIT BUTTON) ---
elif choice == "🔄 Update & Delete":
    st.title("🔄 Update or Delete Ticket")
    df = get_data()
    
    if not df.empty:
        ticket_options = {f"{row['ticket_number']} - {row['summary']}": row['ticket_number'] for _, row in df.iterrows()}
        selected_option = st.selectbox("Select Ticket", list(ticket_options.keys()))
        t_id = ticket_options[selected_option]
        
        row = df[df['ticket_number'] == t_id].iloc[0]
        
        # Form එක ආරම්භය
        with st.form("update_form_new"):
            col1, col2 = st.columns(2)
            
            u_status = col1.selectbox("Status", ["Open", "In Progress", "Pending", "Resolved", "Closed"], 
                                    index=["Open", "In Progress", "Pending", "Resolved", "Closed"].index(row['status']))
            
            u_assign = col1.selectbox("Re-assign To", ["Udara", "Supun", "Madushan", "Technician"],
                                    index=["Udara", "Supun", "Madushan", "Technician"].index(row['assigned_to']) if row['assigned_to'] in ["Udara", "Supun", "Madushan", "Technician"] else 0)
            
            u_prio = col2.selectbox("Change Priority", ["Low", "Medium", "High", "Urgent"],
                                   index=["Low", "Medium", "High", "Urgent"].index(row['priority']))
            
            # --- FIX FOR NaTType ERROR ---
            # දිනයක් නොමැති නම් අද දිනය ලබා ගනී
            try:
                # due_on හෝ due_date යන දෙකෙන් පවතින එක පරීක්ෂා කරයි
                db_date = row.get('due_on') if row.get('due_on') else row.get('due_date')
                if pd.isna(db_date) or db_date == "" or db_date == "None":
                    current_due_date = datetime.now().date()
                else:
                    current_due_date = pd.to_datetime(db_date).date()
            except:
                current_due_date = datetime.now().date()
                
            u_due_date = col2.date_input("Update Due Date", value=current_due_date)
            
            u_remarks = st.text_area("Resolution Remarks", value=str(row['remarks'] if row['remarks'] else ""))
            
            # --- FIX FOR MISSING SUBMIT BUTTON ---
            submit_update = st.form_submit_button("✅ Save Changes")
            
            if submit_update:
                closed_on = str(row['closed_on'])
                res_time = str(row['time_to_resolve'])
                t_spent = str(row['time_spent_min'])
                
                now = datetime.now()
                if u_status in ["Resolved", "Closed"]:
                    if not row['closed_on'] or row['closed_on'] == "":
                        closed_on = now.strftime("%Y-%m-%d %H:%M")
                        try:
                            start = datetime.strptime(row['created_on'], "%Y-%m-%d %H:%M")
                            diff = now - start
                            sec = int(diff.total_seconds())
                            res_time = f"{sec//86400}d {(sec%86400)//3600}h {(sec%3600)//60}m"
                            t_spent = str(sec // 60)
                        except:
                            res_time = "N/A"
                
                # Update SQL (due_on ලෙස භාවිතා කර ඇත)
                conn = sqlite3.connect(DB_NAME); c = conn.cursor()
                c.execute("""UPDATE tickets SET 
                             status=?, assigned_to=?, priority=?, due_on=?,
                             time_spent_min=?, closed_on=?, time_to_resolve=?, remarks=? 
                             WHERE ticket_number=?""",
                          (u_status, u_assign, u_prio, str(u_due_date), t_spent, closed_on, res_time, u_remarks, t_id))
                conn.commit(); conn.close()
                st.toast(f"Ticket {t_id} updated!", icon='✅')
                time.sleep(1); st.rerun()

        # Delete section remains the same
        st.subheader("⚠️ Danger Zone")
        confirm_delete = st.checkbox(f"Confirm deletion of Ticket {t_id}")
        if st.button("🗑️ Delete Ticket permanently", disabled=not confirm_delete):
            conn = sqlite3.connect(DB_NAME); c = conn.cursor()
            c.execute("DELETE FROM tickets WHERE ticket_number=?", (t_id,))
            conn.commit(); conn.close()
            st.warning(f"Ticket {t_id} removed.")
            time.sleep(1); st.rerun()

# --- 9. REPORTS ---
elif choice == "📈 Reports":
    st.title("📈 Operational Performance Reports")
    df = get_data()
    
    if not df.empty:
        # Range (Date Filter)
        df['created_on_dt'] = pd.to_datetime(df['created_on']).dt.date
        col_f1, col_f2 = st.columns(2)
        start_date = col_f1.date_input("Start Date", df['created_on_dt'].min())
        end_date = col_f2.date_input("End Date", df['created_on_dt'].max())
        
        mask = (df['created_on_dt'] >= start_date) & (df['created_on_dt'] <= end_date)
        report_df = df.loc[mask]

        # 2. Executive Summary Cards
        st.subheader("📋 Summary for the period")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Total Tickets", len(report_df))
        r2.metric("Total Resolved", len(report_df[report_df['status'].isin(['Resolved', 'Closed'])]))
        
        # Average resolve time cal (Minutes)
        avg_time = pd.to_numeric(report_df['time_spent_min'], errors='coerce').mean()
        r3.metric("Average Time", f"{avg_time:.1f} Min" if not pd.isna(avg_time) else "N/A")
        
        #(Top Category)
        top_cat = report_df['category'].mode()[0] if not report_df['category'].empty else "N/A"
        r4.metric("Main Issue", top_cat)

        st.divider()

        # 3. Visual Analysis for Reports
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.plotly_chart(px.bar(report_df, x='assigned_to', color='status', 
                                   title="Technician Performance", barmode='stack'), use_container_width=True)
        with col_c2:
            st.plotly_chart(px.histogram(report_df, x='category', title="Issue Categorization"), use_container_width=True)

        st.divider()

        # 4. Data Table & Export
        st.subheader("📄 Detailed Data Log")
        st.dataframe(report_df.drop(columns=['created_on_dt']), use_container_width=True)

        # Excel Download Button
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            report_df.to_excel(writer, index=False, sheet_name='Ticket Report')
        
        st.download_button(
            label="📥 Download this report as Excel (XLSX)",
            data=output.getvalue(),
            file_name=f"Ticket_Report_{start_date}_to_{end_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No records available to create a report.")

# --- 10. SETTINGS (Admin Password & User Creation) ---
elif choice == "⚙️ Settings":
    st.title("⚙️ System Settings")
    
    # Change Password
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

    # Create New User
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
