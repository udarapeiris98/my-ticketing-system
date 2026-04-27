import streamlit as st

# Toolbar එක සහ GitHub Icon එක සැඟවීමට CSS
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
import streamlit as st
# මෙය ඔබේ කේතයේ මුලින්ම තිබිය යුතුය
st.set_page_config(
    page_title="Star Packaging - Ticketing System",
    page_icon="🎫",
    layout="centered"  # "wide" වෙනුවට "centered" යොදන්න
)   

import pandas as pd
from supabase import create_client
from datetime import datetime, date, timedelta
import time
import plotly.express as px
import io

# --- 1. SUPABASE CONNECTION ---
# ඔබගේ Supabase Settings -> API වෙතින් ලැබුණු URL සහ Key මෙහි ඇතුළත් කරන්න
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

def get_users():
    try:
        response = supabase.table("users").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return pd.DataFrame()

# --- LOGIN LOGIC ---
if st.button("Login"):
    res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
    
    if len(res.data) > 0:
        user_info = res.data[0]
        st.session_state['logged_in'] = True
        st.session_state['current_user'] = u
        
        # Database එකේ ඇතිPermissions Session State එකට ලබා ගැනීම
        st.session_state['can_create'] = user_info.get('can_create_ticket', False)
        st.session_state['can_update'] = user_info.get('can_update_ticket', False)
        st.session_state['is_admin'] = user_info.get('is_admin', False)
        
        st.success(f"Welcome {u}!")
        time.sleep(1)
        st.rerun()
    else:
        st.error("Invalid Username or Password")

# --- SIDEBAR MENU ---
if st.session_state.get('logged_in'):
    menu_options = ["🏠 Home"]

    # is_admin TRUE නම් හෝ අදාළ අවසරය තිබේ නම් පමණක් මෙනුව පෙන්වයි
    if st.session_state.get('can_create') or st.session_state.get('is_admin'):
        menu_options.append("🎫 Create Ticket")

    if st.session_state.get('can_update') or st.session_state.get('is_admin'):
        menu_options.append("🔄 Update & Delete")

    # Reports සහ Settings පෙනෙන්නේ IS_ADMIN = TRUE අයට පමණි
    if st.session_state.get('is_admin'):
        menu_options.append("📈 Reports")
        menu_options.append("⚙️ Settings")

    menu_options.append("🚪 Logout")
    choice = st.sidebar.selectbox("Menu", menu_options)

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

# --- 8. UPDATE & DELETE ---
elif choice == "🔄 Update & Delete":
    st.title("🔄 Update or Delete Ticket")
    df = get_data()
    
    if not df.empty:
        # ටිකට් තෝරාගැනීම සඳහා ලැයිස්තුව සෑදීම
        ticket_options = {f"{row['ticket_number']} - {row['summary']}": row['ticket_number'] for _, row in df.iterrows()}
        selected_option = st.selectbox("Select Ticket", list(ticket_options.keys()))
        t_id = ticket_options[selected_option]
        
        row = df[df['ticket_number'] == t_id].iloc[0]
        
        # Form එක ආරම්භය
        with st.form("update_form_new"):
            col1, col2 = st.columns(2)
            
            # පවතින අගයන් ලබා ගැනීම
            u_status = col1.selectbox("Status", ["Open", "In Progress", "Pending", "Resolved", "Closed"], 
                                    index=["Open", "In Progress", "Pending", "Resolved", "Closed"].index(row['status']))
            
            technicians = ["Udara", "Supun", "Madushan", "Technician"]
            u_assign = col1.selectbox("Re-assign To", technicians,
                                    index=technicians.index(row['assigned_to']) if row['assigned_to'] in technicians else 0)
            
            u_prio = col2.selectbox("Change Priority", ["Low", "Medium", "High", "Urgent"],
                                   index=["Low", "Medium", "High", "Urgent"].index(row['priority']))
            
            # --- දින වකවානු පරීක්ෂාව ---
            try:
                db_date = row.get('due_on')
                if pd.isna(db_date) or db_date == "" or db_date == "None" or db_date is None:
                    current_due_date = datetime.now().date()
                else:
                    current_due_date = pd.to_datetime(db_date).date()
            except:
                current_due_date = datetime.now().date()
                
            u_due_date = col2.date_input("Update Due Date", value=current_due_date)
            u_remarks = st.text_area("Resolution Remarks", value=str(row['remarks'] if row['remarks'] else ""))
            
            submit_update = st.form_submit_button("✅ Save Changes")
            
            if submit_update:
                # කලින් තිබූ අගයන් ලබා ගැනීම
                closed_on = str(row['closed_on']) if row['closed_on'] else ""
                res_time = str(row['time_to_resolve']) if row['time_to_resolve'] else ""
                t_spent = str(row['time_spent_min']) if row['time_spent_min'] else "0"
                
                now = datetime.now()
                # ටිකට් එක Resolve/Close කළහොත් කාලය ගණනය කිරීම
                if u_status in ["Resolved", "Closed"]:
                    if not row['closed_on'] or row['closed_on'] == "" or row['closed_on'] == "None":
                        closed_on = now.strftime("%Y-%m-%d %H:%M")
                        try:
                            start = datetime.strptime(str(row['created_on']), "%Y-%m-%d %H:%M")
                            diff = now - start
                            sec = int(diff.total_seconds())
                            res_time = f"{sec//86400}d {(sec%86400)//3600}h {(sec%3600)//60}m"
                            t_spent = str(sec // 60)
                        except:
                            res_time = "N/A"
                
                # --- Supabase Update එක සිදු කරන ආකාරය ---
                try:
                    update_data = {
                        "status": u_status,
                        "assigned_to": u_assign,
                        "priority": u_prio,
                        "due_on": str(u_due_date),
                        "time_spent_min": t_spent,
                        "closed_on": closed_on,
                        "time_to_resolve": res_time,
                        "remarks": u_remarks
                    }
                    
                    supabase.table("tickets").update(update_data).eq("ticket_number", t_id).execute()
                    
                    st.toast(f"Ticket {t_id} updated in Supabase!", icon='✅')
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Update Error: {e}")

        # Delete Section
        st.subheader("⚠️ Warning !")
        confirm_delete = st.checkbox(f"Confirm deletion of Ticket {t_id}")
        if st.button("🗑️ Delete Ticket permanently", disabled=not confirm_delete):
            try:
                # Supabase Delete එක සිදු කරන ආකාරය
                supabase.table("tickets").delete().eq("ticket_number", t_id).execute()
                
                st.warning(f"Ticket {t_id} removed from Supabase.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Delete Error: {e}")
    else:
        st.info("No records available to update.")

# --- 9. REPORTS ---
elif choice == "📈 Reports":
    st.title("📈 Operational Performance Reports")
    
    # දත්ත ලබා ගැනීම (get_data() ශ්‍රිතය Supabase සඳහා සකසා ඇති බව උපකල්පනය කෙරේ)
    df = get_data()
    
    if not df.empty:
        # 1. දින වකවානු සකස් කිරීම (Supabase හි TEXT ලෙස ඇති දින Date objects බවට පත් කිරීම)
        df['created_on_dt'] = pd.to_datetime(df['created_on']).dt.date
        
        # Range (Date Filter)
        col_f1, col_f2 = st.columns(2)
        min_date = df['created_on_dt'].min()
        max_date = df['created_on_dt'].max()
        
        start_date = col_f1.date_input("Start Date", min_date)
        end_date = col_f2.date_input("End Date", max_date)
        
        # දත්ත Filter කිරීම
        mask = (df['created_on_dt'] >= start_date) & (df['created_on_dt'] <= end_date)
        report_df = df.loc[mask].copy() # Original df එකට හානි නොවීමට copy එකක් ගනු ලැබේ

        if not report_df.empty:
            # 2. Executive Summary Cards
            st.subheader("📋 Summary for the period")
            r1, r2, r3, r4 = st.columns(4)
            
            r1.metric("Total Tickets", len(report_df))
            
            # Resolved/Closed ටිකට් ප්‍රමාණය
            resolved_count = len(report_df[report_df['status'].isin(['Resolved', 'Closed'])])
            r2.metric("Total Resolved", resolved_count)
            
            # සාමාන්‍ය විසඳුම් කාලය (Average resolve time)
            # Supabase වල මෙය TEXT ලෙස තිබිය හැකි බැවින් NUMERIC බවට පත් කරයි
            avg_time = pd.to_numeric(report_df['time_spent_min'], errors='coerce').mean()
            r3.metric("Average Time", f"{avg_time:.1f} Min" if not pd.isna(avg_time) else "0.0 Min")
            
            # වැඩිපුරම ලැබුණු ගැටලු වර්ගය (Top Category)
            if not report_df['category'].dropna().empty:
                top_cat = report_df['category'].mode()[0]
            else:
                top_cat = "N/A"
            r4.metric("Main Issue", top_cat)

            st.divider()

            # 3. Visual Analysis for Reports
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                fig1 = px.bar(report_df, x='assigned_to', color='status', 
                             title="Technician Performance", 
                             barmode='stack',
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig1, use_container_width=True)
                
            with col_c2:
                fig2 = px.histogram(report_df, x='category', 
                                   title="Issue Categorization",
                                   color_discrete_sequence=['#636EFA'])
                st.plotly_chart(fig2, use_container_width=True)

            st.divider()

            # 4. Data Table & Export
            st.subheader("📄 Detailed Data Log")
            # පෙන්වීමට අනවශ්‍ය columns ඉවත් කිරීම (ඇත්නම් පමණක්)
            display_df = report_df.drop(columns=['created_on_dt']) if 'created_on_dt' in report_df.columns else report_df
            st.dataframe(display_df, use_container_width=True)

            # Excel Download Button
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    report_df.to_excel(writer, index=False, sheet_name='Ticket Report')
                
                st.download_button(
                    label="📥 Download this report as Excel (XLSX)",
                    data=output.getvalue(),
                    file_name=f"Ticket_Report_{start_date}_to_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Excel generation error: {e}")
        else:
            st.warning("තෝරාගත් කාලසීමාව සඳහා දත්ත කිසිවක් නැත.")
    else:
        st.info("No records available to create a report.")

# --- ⚙️ SETTINGS SECTION (REPLACE YOUR OLD SETTINGS CODE WITH THIS) ---
elif choice == "⚙️ Settings":
    st.title("⚙️ System Settings")
    st.markdown("---")

    # 🔑 1. Password Change Section
    st.subheader("🔑 Change Your Password")
    with st.form("change_pass_form"):
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Update Password"):
            if new_pass == confirm_pass and new_pass != "":
                try:
                    supabase.table("users").update({"password": new_pass}).eq("username", st.session_state['current_user']).execute()
                    st.success("✅ Password updated successfully!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Passwords do not match or are empty!")

    st.write("")
    st.markdown("---")
    st.write("")

    # 👤 2. Create New User with Permissions Section
    st.subheader("👤 Create New User with Permissions")
    with st.form("create_user_form", clear_on_submit=True):
        new_username = st.text_input("New Username")
        new_user_pass = st.text_input("New User Password", type="password")
        
        st.write("**Assign Access Level / Permissions:**")
        
        # Columns භාවිතයෙන් Checkboxes ලස්සනට පෙළගැස්වීම
        col1, col2, col3 = st.columns(3)
        c_create = col1.checkbox("Can Create Ticket", help="Allow user to add new tickets")
        c_update = col2.checkbox("Can Update Ticket", help="Allow user to update existing tickets")
        c_admin = col3.checkbox("Is System Admin", help="Full access to Reports and Settings")
        
        submit_user = st.form_submit_button("Create User")
        
        if submit_user:
            if new_username and new_user_pass:
                try:
                    # Supabase වෙත දත්ත යැවීම
                    user_data = {
                        "username": new_username, 
                        "password": new_user_pass,
                        "can_create_ticket": c_create,
                        "can_update_ticket": c_update,
                        "is_admin": c_admin
                    }
                    supabase.table("users").insert(user_data).execute()
                    st.success(f"✅ User '{new_username}' created successfully!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Please provide both Username and Password!")

    # 📋 3. Optional: දැනට සිටින පරිශීලකයින් බැලීම (Admin Only)
    st.markdown("---")
    if st.checkbox("Show Existing Users"):
        try:
            users_list = supabase.table("users").select("username, can_create_ticket, can_update_ticket, is_admin").execute()
            st.table(users_list.data)
        except:
            pass
