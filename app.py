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

# --- 1. SUPABASE SETUP (CLOUD DATABASE) ---
# Streamlit Cloud Secrets හරහා මේවා ලබා ගනී
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- DATABASE FUNCTIONS ---
def get_data():
    response = supabase.table("tickets").select("*").execute()
    return pd.DataFrame(response.data)

def get_users():
    response = supabase.table("users").select("*").execute()
    return response.data

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type='password')
    if st.button("Login"):
        users = get_users()
        user_match = next((item for item in users if item["username"] == u and item["password"] == p), None)
        
        if user_match:
            st.session_state['logged_in'] = True
            st.session_state['current_user'] = u
            st.rerun()
        else: 
            st.error("Invalid Username or Password!")
    st.stop()

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
        with m1: st.metric(label="Total Tickets", value=total)
        with m2: st.metric(label="🔴 Open", value=open_t)
        with m3: st.metric(label="🟠 In Progress", value=prog_t)
        with m4: st.metric(label="🟡 Pending", value=pend_t)
        with m5: st.metric(label="🟢 Completed", value=comp_t)

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(df, names='status', title="Status Breakdown", hole=0.5)
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            fig_bar = px.bar(df, x='priority', color='status', title="Priority Analysis", barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)
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
                data = {
                    "summary": summ, "description": desc, "assigned_to": assigned, "category": cat,
                    "created_on": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "created_by": st.session_state['current_user'], "due_on": str(due),
                    "priority": prio, "organization_name": org, "status": "Open",
                    "time_spent_min": "0", "closed_on": "", "time_to_resolve": "", "remarks": ""
                }
                supabase.table("tickets").insert(data).execute()
                st.success("✅ Ticket submitted successfully!"); time.sleep(1); st.rerun()

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
            u_status = col1.selectbox("Status", ["Open", "In Progress", "Pending", "Resolved", "Closed"], 
                                    index=["Open", "In Progress", "Pending", "Resolved", "Closed"].index(row['status']))
            u_assign = col1.selectbox("Re-assign To", ["Udara", "Supun", "Madushan", "Technician"],
                                    index=["Udara", "Supun", "Madushan", "Technician"].index(row['assigned_to']) if row['assigned_to'] in ["Udara", "Supun", "Madushan", "Technician"] else 0)
            u_prio = col2.selectbox("Change Priority", ["Low", "Medium", "High", "Urgent"],
                                   index=["Low", "Medium", "High", "Urgent"].index(row['priority']))
            
            u_due_date = col2.date_input("Update Due Date", value=pd.to_datetime(row['due_on']).date())
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
                
                update_data = {
                    "status": u_status, "assigned_to": u_assign, "priority": u_prio,
                    "due_on": str(u_due_date), "time_spent_min": t_spent,
                    "closed_on": closed_on, "time_to_resolve": res_time, "remarks": u_remarks
                }
                supabase.table("tickets").update(update_data).eq("ticket_number", t_id).execute()
                st.success(f"Ticket {t_id} updated!"); time.sleep(1); st.rerun()

        if st.session_state['current_user'] == 'admin':
            st.subheader("⚠️ Admin: Delete Ticket")
            if st.button("🗑️ Delete Ticket permanently"):
                supabase.table("tickets").delete().eq("ticket_number", t_id).execute()
                st.warning(f"Ticket {t_id} removed."); time.sleep(1); st.rerun()

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
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            report_df.to_excel(writer, index=False, sheet_name='Ticket Report')
        st.download_button(label="📥 Download Excel", data=output.getvalue(), file_name="Report.xlsx")
    else: st.info("No records available.")

# --- 10. SETTINGS (ADMIN ONLY) ---
elif choice == "⚙️ Settings":
    st.title("⚙️ System Settings")
    
    # 🔑 Password වෙනස් කිරීමේ කොටස
    st.subheader("🔑 Change My Password")
    with st.form("change_pass_form"):
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update Password"):
            if new_pass == confirm_pass and new_pass != "":
                # Supabase එකේ වත්මන් පරිශීලකයාගේ පාස්වර්ඩ් එක Update කිරීම
                supabase.table("users").update({"password": new_pass}).eq("username", st.session_state['current_user']).execute()
                st.success("✅ Your password has been updated!")
            else:
                st.error("❌ Passwords do not match or field is empty!")

    st.divider()
    
    # 👤 අලුත් පරිශීලකයින් සෑදීමේ කොටස
    st.subheader("👤 Create New User")
    with st.form("create_user_form"):
        new_username = st.text_input("New Username")
        new_user_pass = st.text_input("New User Password", type="password")
        if st.form_submit_button("Create User"):
            if new_username and new_user_pass:
                try:
                    # Supabase එකට අලුත් දත්ත ඇතුළත් කිරීම
                    supabase.table("users").insert({"username": new_username, "password": new_user_pass}).execute()
                    st.success(f"✅ User '{new_username}' created successfully!")
                except Exception as e:
                    st.error(f"❌ Error: Username might already exist!")
            else:
                st.error("❌ Please enter both username and password!")
