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

# --- HIDE STREAMLIT DEFAULT TOOLBAR ---
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

# --- 2. HELPER FUNCTIONS ---
def get_data():
    try:
        response = supabase.table("tickets").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching tickets: {e}")
        return pd.DataFrame()


def get_current_user():
    return st.session_state.get("current_user", "")


def is_admin():
    return st.session_state.get("is_admin", False) is True


def can_create_ticket():
    return st.session_state.get("can_create", False) is True or is_admin()


def can_update_ticket():
    return st.session_state.get("can_update", False) is True or is_admin()


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def safe_date(value):
    try:
        if value is None or value == "" or str(value).lower() == "nan":
            return date.today()
        return pd.to_datetime(value).date()
    except Exception:
        return date.today()


# --- 3. SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- 4. LOGIN PAGE ---
if not st.session_state["logged_in"]:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
            if len(res.data) > 0:
                user_info = res.data[0]
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = user_info.get("username", u)
                st.session_state["can_create"] = user_info.get("can_create_ticket", False)
                st.session_state["can_update"] = user_info.get("can_update_ticket", False)
                st.session_state["is_admin"] = user_info.get("is_admin", False)
                st.success(f"Welcome {st.session_state['current_user']}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid Username or Password")
        except Exception as e:
            st.error(f"Login error: {e}")

# --- 5. MAIN APPLICATION ---
else:
    # --- SIDEBAR MENU ---
    menu_options = ["🏠 Home"]

    if can_create_ticket():
        menu_options.append("➕ Create Ticket")

    if can_update_ticket():
        menu_options.append("🔄 Update Ticket")

    if is_admin():
        menu_options.append("🗑️ Delete Ticket")
        menu_options.append("📈 Reports")
        menu_options.append("⚙️ Settings")

    menu_options.append("🚪 Logout")

    choice = st.sidebar.selectbox("Menu", menu_options)

    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 User: **{get_current_user()}**")
    st.sidebar.write(f"🛡️ Admin: **{'Yes' if is_admin() else 'No'}**")

    # --- LOGOUT ---
    if choice == "🚪 Logout":
        logout()

    # --- HOME PAGE ---
    elif choice == "🏠 Home":
        st.title(f"Welcome, {get_current_user()}!")
        st.write("Star Packaging Ticketing System එකට සාදරයෙන් පිළිගනිමු.")

        st.subheader("Your Access")
        col1, col2, col3 = st.columns(3)
        col1.metric("Create Ticket", "Yes" if can_create_ticket() else "No")
        col2.metric("Update Ticket", "Yes" if can_update_ticket() else "No")
        col3.metric("Admin", "Yes" if is_admin() else "No")

    # --- CREATE TICKET ---
    elif choice == "➕ Create Ticket":
        if not can_create_ticket():
            st.error("You do not have permission to create tickets.")
            st.stop()

        st.title("➕ Create New Ticket")

        if "f_key" not in st.session_state:
            st.session_state.f_key = 0

        with st.form(key=f"ticket_form_{st.session_state.f_key}"):
            col1, col2 = st.columns(2)
            summ = col1.text_input("Summary")
            assigned = col1.selectbox("Assign To", ["Udara", "Supun", "Madushan", "Technician"])
            cat = col1.selectbox("Category", ["PC Hardware", "Software", "Network", "Printer", "Email", "CCTV", "Others"])
            prio = col2.selectbox("Priority", ["Low", "Medium", "High", "Urgent"], index=1)
            org = col2.text_input("Organization / Dept")
            due = col2.date_input("Due Date", date.today() + timedelta(days=1))
            desc = st.text_area("Detailed Description")

            if st.form_submit_button("Submit"):
                if not summ.strip():
                    st.error("Summary is required.")
                else:
                    ticket_data = {
                        "summary": summ.strip(),
                        "description": desc.strip(),
                        "assigned_to": assigned,
                        "category": cat,
                        "closed_on": "",
                        "created_on": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "created_by": get_current_user(),
                        "due_on": str(due),
                        "priority": prio,
                        "organization_name": org.strip(),
                        "status": "Open",
                        "time_spent_min": "0",
                        "time_to_resolve": "",
                        "remarks": ""
                    }
                    try:
                        supabase.table("tickets").insert(ticket_data).execute()
                        st.success("✅ Ticket submitted!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # --- UPDATE TICKET ---
    elif choice == "🔄 Update Ticket":
        if not can_update_ticket():
            st.error("You do not have permission to update tickets.")
            st.stop()

        st.title("🔄 Update Ticket")
        df = get_data()

        if df.empty:
            st.info("No records available.")
            st.stop()

        # Normal users can update only their own created tickets.
        # Admin can update all tickets.
        if not is_admin():
            df = df[df["created_by"] == get_current_user()]

        if df.empty:
            st.info("No tickets available for your user account.")
            st.stop()

        ticket_options = {
            f"{row['ticket_number']} - {row['summary']}": row["ticket_number"]
            for _, row in df.iterrows()
        }

        selected_option = st.selectbox("Select Ticket", list(ticket_options.keys()))
        t_id = ticket_options[selected_option]
        row = df[df["ticket_number"] == t_id].iloc[0]

        st.info(f"Selected Ticket: {t_id} | Created By: {row.get('created_by', '')}")

        with st.form("update_form"):
            if is_admin():
                st.subheader("Admin Update")
                col1, col2 = st.columns(2)

                status_list = ["Open", "In Progress", "Pending", "Resolved", "Closed"]
                current_status = row.get("status", "Open")
                status_index = status_list.index(current_status) if current_status in status_list else 0
                u_status = col1.selectbox("Status", status_list, index=status_index)

                technicians = ["Udara", "Supun", "Madushan", "Technician"]
                current_assigned = row.get("assigned_to", "Technician")
                assign_index = technicians.index(current_assigned) if current_assigned in technicians else 0
                u_assign = col1.selectbox("Re-assign To", technicians, index=assign_index)

                priority_list = ["Low", "Medium", "High", "Urgent"]
                current_priority = row.get("priority", "Medium")
                priority_index = priority_list.index(current_priority) if current_priority in priority_list else 1
                u_prio = col2.selectbox("Change Priority", priority_list, index=priority_index)

                u_due_date = col2.date_input("Update Due Date", value=safe_date(row.get("due_on")))
                u_remarks = st.text_area("Resolution Remarks", value=str(row.get("remarks") or ""))

            else:
                st.subheader("User Update")
                st.caption("Normal users can update only Status and Remarks for their own tickets.")

                status_list = ["Open", "In Progress", "Pending", "Resolved"]
                current_status = row.get("status", "Open")
                status_index = status_list.index(current_status) if current_status in status_list else 0
                u_status = st.selectbox("Status", status_list, index=status_index)
                u_remarks = st.text_area("Remarks", value=str(row.get("remarks") or ""))

                # Keep existing values for normal users.
                u_assign = row.get("assigned_to", "")
                u_prio = row.get("priority", "Medium")
                u_due_date = safe_date(row.get("due_on"))

            if st.form_submit_button("✅ Save Changes"):
                closed_on = str(row.get("closed_on") or "")
                res_time = str(row.get("time_to_resolve") or "")
                t_spent = str(row.get("time_spent_min") or "0")

                if u_status in ["Resolved", "Closed"]:
                    if not closed_on:
                        now = datetime.now()
                        closed_on = now.strftime("%Y-%m-%d %H:%M")
                        try:
                            start = datetime.strptime(str(row.get("created_on")), "%Y-%m-%d %H:%M")
                            diff = now - start
                            sec = int(diff.total_seconds())
                            res_time = f"{sec // 86400}d {(sec % 86400) // 3600}h {(sec % 3600) // 60}m"
                            t_spent = str(sec // 60)
                        except Exception:
                            res_time = "N/A"

                update_data = {
                    "status": u_status,
                    "remarks": u_remarks,
                    "closed_on": closed_on,
                    "time_to_resolve": res_time,
                    "time_spent_min": t_spent
                }

                # Only Admin can update assignment, priority, and due date.
                if is_admin():
                    update_data.update({
                        "assigned_to": u_assign,
                        "priority": u_prio,
                        "due_on": str(u_due_date)
                    })

                try:
                    supabase.table("tickets").update(update_data).eq("ticket_number", t_id).execute()
                    st.success(f"✅ Ticket {t_id} updated!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Update Error: {e}")

    # --- DELETE TICKET - ADMIN ONLY ---
    elif choice == "🗑️ Delete Ticket":
        if not is_admin():
            st.error("Only admin can delete tickets.")
            st.stop()

        st.title("🗑️ Delete Ticket")
        df = get_data()

        if df.empty:
            st.info("No records available.")
            st.stop()

        ticket_options = {
            f"{row['ticket_number']} - {row['summary']}": row["ticket_number"]
            for _, row in df.iterrows()
        }

        selected_option = st.selectbox("Select Ticket to Delete", list(ticket_options.keys()))
        t_id = ticket_options[selected_option]

        st.warning("This action will remove the selected ticket permanently from the table.")
        confirm_delete = st.checkbox(f"Confirm deletion of Ticket {t_id}")

        if st.button("🗑️ Delete Ticket", disabled=not confirm_delete):
            try:
                supabase.table("tickets").delete().eq("ticket_number", t_id).execute()
                st.success(f"Ticket {t_id} removed.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Delete Error: {e}")

    # --- REPORTS - ADMIN ONLY ---
    elif choice == "📈 Reports":
        if not is_admin():
            st.error("Only admin can view reports.")
            st.stop()

        st.title("📈 Performance Reports")
        df = get_data()

        if df.empty:
            st.info("No records available.")
            st.stop()

        try:
            df["created_on_dt"] = pd.to_datetime(df["created_on"], errors="coerce").dt.date
            df = df.dropna(subset=["created_on_dt"])

            if df.empty:
                st.warning("No valid created date data available.")
                st.stop()

            col_f1, col_f2 = st.columns(2)
            start_date = col_f1.date_input("Start Date", df["created_on_dt"].min())
            end_date = col_f2.date_input("End Date", df["created_on_dt"].max())

            report_df = df[(df["created_on_dt"] >= start_date) & (df["created_on_dt"] <= end_date)]

            if not report_df.empty:
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Total Tickets", len(report_df))
                r2.metric("Resolved", len(report_df[report_df["status"].isin(["Resolved", "Closed"])]))
                avg_time = pd.to_numeric(report_df["time_spent_min"], errors="coerce").mean()
                r3.metric("Avg Time", f"{avg_time:.1f} Min" if not pd.isna(avg_time) else "0.0 Min")
                r4.metric("Top Issue", report_df["category"].mode()[0] if not report_df["category"].empty else "N/A")

                st.dataframe(report_df, use_container_width=True)

                st.subheader("Charts")
                status_count = report_df["status"].value_counts().reset_index()
                status_count.columns = ["Status", "Count"]
                fig_status = px.bar(status_count, x="Status", y="Count", title="Tickets by Status")
                st.plotly_chart(fig_status, use_container_width=True)

                cat_count = report_df["category"].value_counts().reset_index()
                cat_count.columns = ["Category", "Count"]
                fig_cat = px.pie(cat_count, names="Category", values="Count", title="Tickets by Category")
                st.plotly_chart(fig_cat, use_container_width=True)

                csv_buffer = io.StringIO()
                report_df.to_csv(csv_buffer, index=False)
                st.download_button(
                    "⬇️ Download Report CSV",
                    data=csv_buffer.getvalue(),
                    file_name="ticket_report.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data for selected range.")
        except Exception as e:
            st.error(f"Report error: {e}")

    # --- SETTINGS - ADMIN ONLY ---
    elif choice == "⚙️ Settings":
        if not is_admin():
            st.error("Only admin can access settings.")
            st.stop()

        st.title("⚙️ System Settings")
        st.markdown("---")

        st.subheader("🔑 Change Your Password")
        with st.form("change_pass_form"):
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm New Password", type="password")

            if st.form_submit_button("Update Password"):
                if new_pass == confirm_pass and new_pass.strip() != "":
                    try:
                        supabase.table("users").update({"password": new_pass}).eq("username", get_current_user()).execute()
                        st.success("✅ Password updated successfully!")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.error("❌ Passwords do not match or password is empty!")

        st.divider()

        st.subheader("👤 Create New User")
        with st.form("create_user_form", clear_on_submit=True):
            new_username = st.text_input("New Username")
            new_user_pass = st.text_input("New User Password", type="password")

            st.write("**Assign Access Level:**")
            col1, col2, col3 = st.columns(3)
            c_create = col1.checkbox("Can Create Ticket", value=True)
            c_update = col2.checkbox("Can Update Ticket", value=True)
            c_admin = col3.checkbox("Is System Admin", value=False)

            if c_admin:
                st.info("Admin users automatically get full access.")

            if st.form_submit_button("Create User"):
                if new_username.strip() and new_user_pass.strip():
                    try:
                        user_data = {
                            "username": new_username.strip(),
                            "password": new_user_pass,
                            "can_create_ticket": True if c_admin else c_create,
                            "can_update_ticket": True if c_admin else c_update,
                            "is_admin": c_admin
                        }
                        supabase.table("users").insert(user_data).execute()
                        st.success(f"✅ User '{new_username}' created!")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.error("Username and password are required.")

        st.divider()

        st.subheader("👥 Existing Users")
        if st.button("Refresh Users List"):
            st.rerun()

        try:
            users_list = supabase.table("users").select(
                "username, can_create_ticket, can_update_ticket, is_admin"
            ).execute()
            st.table(users_list.data)
        except Exception as e:
            st.error(f"Could not load users: {e}")
