import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, date, timedelta
import time
import plotly.express as px
import io

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Star Packaging - Ticketing System",
    page_icon="🎫",
    layout="centered"
)

# Toolbar එක සැඟවීමට CSS
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 1. SUPABASE CONNECTION ---
URL = "https://tfyulwcbjnmrecrukzsm.supabase.co" 
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

# --- 3. SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 4. LOGIN LOGIC ---
if not st.session_state['logged_in']:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    
    if st.button("Login"):
        res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
        if len(res.data) > 0:
            user_info = res.data[0]
            st.session_state['logged_in'] = True
            st.session_state['current_user'] = u
            # Database එකේ ඇති අගයන් Session එකට ලබා ගැනීම
            st.session_state['can_create'] = user_info.get('can_create_ticket', False)
            st.session_state['can_update'] = user_info.get('can_update_ticket', False)
            st.session_state['is_admin'] = user_info.get('is_admin', False)
            st.success(f"Welcome {u}!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Invalid Username or Password")

# --- 5. MAIN APPLICATION (AFTER LOGIN) ---
else:
 # --- SIDEBAR MENU (අවසරයන් හරියටම වෙන් කිරීම) ---
    menu_options = ["🏠 Home"]
    
    # 1. ටිකට් සෑදීමේ අවසරය ඇත්නම් පමණක් පෙන්වන්න
    if st.session_state.get('can_create') == True or st.session_state.get('is_admin') == True:
        menu_options.append("➕ Create Ticket")
        
    # 2. ටිකට් යාවත්කාලීන කිරීමේ අවසරය ඇත්නම් පමණක් පෙන්වන්න
    if st.session_state.get('can_update') == True or st.session_state.get('is_admin') == True:
        menu_options.append("🔄 Update & Delete")
        
    # 3. Reports සහ Settings පෙන්විය යුත්තේ Admin ට පමණි
    if st.session_state.get('is_admin') == True:
        menu_options.append("📈 Reports")
        menu_options.append("⚙️ Settings")
        
    menu_options.append("🚪 Logout")
    
    choice = st.sidebar.selectbox("Menu", menu_options)
    choice = st.sidebar.selectbox("Menu", menu_options)

    # --- Logout Logic ---
    if choice == "🚪 Logout":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # --- Home Page ---
    elif choice == "🏠 Home":
        st.title(f"Welcome, {st.session_state['current_user']}!")
        st.write("Star Packaging Ticketing System එකට සාදරයෙන් පිළිගනිමු.")

    # --- CREATE TICKET ---
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
                        st.success("✅ Ticket submitted!"); time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

    # --- UPDATE & DELETE ---
    elif choice == "🔄 Update & Delete":
        st.title("🔄 Update or Delete Ticket")
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
                technicians = ["Udara", "Supun", "Madushan", "Technician"]
                u_assign = col1.selectbox("Re-assign To", technicians,
                                        index=technicians.index(row['assigned_to']) if row['assigned_to'] in technicians else 0)
                u_prio = col2.selectbox("Change Priority", ["Low", "Medium", "High", "Urgent"],
                                       index=["Low", "Medium", "High", "Urgent"].index(row['priority']))
                
                db_date = row.get('due_on')
                current_due_date = pd.to_datetime(db_date).date() if db_date else datetime.now().date()
                u_due_date = col2.date_input("Update Due Date", value=current_due_date)
                u_remarks = st.text_area("Resolution Remarks", value=str(row['remarks'] if row['remarks'] else ""))
                
                if st.form_submit_button("✅ Save Changes"):
                    closed_on = str(row['closed_on']) if row['closed_on'] else ""
                    res_time = str(row['time_to_resolve']) if row['time_to_resolve'] else ""
                    t_spent = str(row['time_spent_min']) if row['time_spent_min'] else "0"
                    
                    if u_status in ["Resolved", "Closed"]:
                        if not row['closed_on'] or row['closed_on'] == "":
                            now = datetime.now()
                            closed_on = now.strftime("%Y-%m-%d %H:%M")
                            try:
                                start = datetime.strptime(str(row['created_on']), "%Y-%m-%d %H:%M")
                                diff = now - start
                                sec = int(diff.total_seconds())
                                res_time = f"{sec//86400}d {(sec%86400)//3600}h {(sec%3600)//60}m"
                                t_spent = str(sec // 60)
                            except: res_time = "N/A"
                    
                    try:
                        update_data = {"status": u_status, "assigned_to": u_assign, "priority": u_prio,
                                     "due_on": str(u_due_date), "time_spent_min": t_spent,
                                     "closed_on": closed_on, "time_to_resolve": res_time, "remarks": u_remarks}
                        supabase.table("tickets").update(update_data).eq("ticket_number", t_id).execute()
                        st.success(f"Ticket {t_id} updated!")
                        time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Update Error: {e}")

            # Delete function එක Admin ට පමණක් සීමා කිරීම වඩාත් ආරක්ෂිතයි
            if st.session_state.get('is_admin'):
                st.subheader("⚠️ Danger Zone")
                confirm_delete = st.checkbox(f"Confirm deletion of Ticket {t_id}")
                if st.button("🗑️ Delete Ticket", disabled=not confirm_delete):
                    try:
                        supabase.table("tickets").delete().eq("ticket_number", t_id).execute()
                        st.warning(f"Ticket {t_id} removed.")
                        time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Delete Error: {e}")
        else: st.info("No records available.")

    # --- REPORTS ---
    elif choice == "📈 Reports":
        st.title("📈 Performance Reports")
        df = get_data()
        if not df.empty:
            df['created_on_dt'] = pd.to_datetime(df['created_on']).dt.date
            col_f1, col_f2 = st.columns(2)
            start_date = col_f1.date_input("Start Date", df['created_on_dt'].min())
            end_date = col_f2.date_input("End Date", df['created_on_dt'].max())
            report_df = df[(df['created_on_dt'] >= start_date) & (df['created_on_dt'] <= end_date)]

            if not report_df.empty:
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Total Tickets", len(report_df))
                r2.metric("Resolved", len(report_df[report_df['status'].isin(['Resolved', 'Closed'])]))
                avg_time = pd.to_numeric(report_df['time_spent_min'], errors='coerce').mean()
                r3.metric("Avg Time", f"{avg_time:.1f} Min" if not pd.isna(avg_time) else "0.0 Min")
                r4.metric("Top Issue", report_df['category'].mode()[0] if not report_df['category'].empty else "N/A")
                st.dataframe(report_df, use_container_width=True)
            else: st.warning("No data for selected range.")

    # --- SETTINGS SECTION ---
    elif choice == "⚙️ Settings":
        st.title("⚙️ System Settings")
        st.markdown("---")

        st.subheader("🔑 Change Your Password")
        with st.form("change_pass_form"):
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Update Password"):
                if new_pass == confirm_pass and new_pass != "":
                    try:
                        supabase.table("users").update({"password": new_pass}).eq("username", st.session_state['current_user']).execute()
                        st.success("✅ Password updated successfully!")
                    except Exception as e: st.error(f"❌ Error: {e}")
                else: st.error("❌ Passwords do not match!")

        st.divider()

        st.subheader("👤 Create New User")
        with st.form("create_user_form", clear_on_submit=True):
            new_username = st.text_input("New Username")
            new_user_pass = st.text_input("New User Password", type="password")
            st.write("**Assign Access Level:**")
            col1, col2, col3 = st.columns(3)
            c_create = col1.checkbox("Can Create Ticket")
            c_update = col2.checkbox("Can Update Ticket")
            c_admin = col3.checkbox("Is System Admin")
            
            if st.form_submit_button("Create User"):
                if new_username and new_user_pass:
                    try:
                        user_data = {
                            "username": new_username, "password": new_user_pass,
                            "can_create_ticket": c_create, "can_update_ticket": c_update, "is_admin": c_admin
                        }
                        supabase.table("users").insert(user_data).execute()
                        st.success(f"✅ User '{new_username}' created!")
                    except Exception as e: st.error(f"❌ Error: {e}")

        if st.checkbox("Show Existing Users"):
            try:
                users_list = supabase.table("users").select("username, can_create_ticket, can_update_ticket, is_admin").execute()
                st.table(users_list.data)
            except: pass
