import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime,date,timedelta
import time

##########################################
# SUPABASE
##########################################

URL="YOUR_SUPABASE_URL"
KEY="YOUR_SUPABASE_KEY"

supabase=create_client(URL,KEY)

st.set_page_config(
page_title="Ticketing System",
page_icon="🎫"
)

##########################################
# FUNCTIONS
##########################################

def get_data():
    data=supabase.table("tickets").select("*").execute()
    return pd.DataFrame(data.data)


def is_admin():
    return st.session_state.get("is_admin",False)


def can_create():
    return st.session_state.get("can_create",False) or is_admin()


def can_update():
    return st.session_state.get("can_update",False) or is_admin()


def logout():
    st.session_state.clear()
    st.rerun()


##########################################
# SESSION
##########################################

if "logged_in" not in st.session_state:
    st.session_state.logged_in=False


##########################################
# LOGIN
##########################################

if not st.session_state.logged_in:

    st.title("Login")

    u=st.text_input("Username")
    p=st.text_input("Password",type="password")

    if st.button("Login"):

        res=supabase.table("users")\
        .select("*")\
        .eq("username",u)\
        .eq("password",p)\
        .execute()

        if len(res.data)>0:

            user=res.data[0]

            st.session_state.logged_in=True
            st.session_state.current_user=user["username"]

            st.session_state.can_create=user["can_create_ticket"]
            st.session_state.can_update=user["can_update_ticket"]
            st.session_state.is_admin=user["is_admin"]

            st.success("Login Success")
            time.sleep(1)
            st.rerun()

        else:
            st.error("Invalid login")


##########################################
# MAIN
##########################################

else:

    menu=["Home"]

    if can_create():
        menu.append("Create Ticket")

    if can_update():
        menu.append("Update Ticket")

    if is_admin():
        menu.append("Delete Ticket")
        menu.append("Reports")
        menu.append("Settings")

    menu.append("Logout")

    choice=st.sidebar.selectbox(
        "Menu",
        menu
    )


##########################################
# HOME
##########################################

    if choice=="Home":

        st.title(
        f"Welcome {st.session_state.current_user}"
        )

        c1,c2,c3=st.columns(3)

        c1.metric(
        "Create",
        "Yes" if can_create() else "No"
        )

        c2.metric(
        "Update",
        "Yes" if can_update() else "No"
        )

        c3.metric(
        "Admin",
        "Yes" if is_admin() else "No"
        )


##########################################
# CREATE
##########################################

    elif choice=="Create Ticket":

        st.title("Create Ticket")

        with st.form("ticketform"):

            summary=st.text_input("Summary")

            desc=st.text_area(
            "Description"
            )

            cat=st.selectbox(
            "Category",
            [
            "Hardware",
            "Software",
            "Network",
            "Printer"
            ])

            priority=st.selectbox(
            "Priority",
            [
            "Low",
            "Medium",
            "High"
            ])

            assigned=st.selectbox(
            "Assign To",
            [
            "Technician",
            "Udara",
            "Supun"
            ])

            due=st.date_input(
            "Due Date",
            date.today()+timedelta(days=1)
            )

            if st.form_submit_button(
            "Submit"
            ):

            data = {
 "summary": summary,
 "description": desc,
 "category": cat,
 "priority": priority,
 "assigned_to": assigned,
 "organization_name": org,
 "status":"Open",
 "created_by": st.session_state.current_user,
 "due_on": str(due),

}

                }

                supabase.table(
                "tickets"
                ).insert(data).execute()

                st.success(
                "Ticket Created"
                )


##########################################
# UPDATE
##########################################

    elif choice=="Update Ticket":

        st.title(
        "Update Ticket"
        )

        df=get_data()

        if not is_admin():

            df=df[
            df["created_by"]==
            st.session_state.current_user
            ]

        if len(df)==0:
            st.warning("No Tickets")
            st.stop()

        options={
        f'{r["ticket_number"]}-{r["summary"]}':
        r["ticket_number"]
        for _,r in df.iterrows()
        }

        selected=st.selectbox(
        "Select",
        list(options.keys())
        )

        tid=options[selected]

        row=df[
        df.ticket_number==tid
        ].iloc[0]


        if is_admin():

            with st.form("adminupdate"):

                status=st.selectbox(
                "Status",
                [
                "Open",
                "In Progress",
                "Resolved",
                "Closed"
                ])

                assign=st.text_input(
                "Assign",
                row["assigned_to"]
                )

                remarks=st.text_area(
                "Remarks"
                )

                if st.form_submit_button(
                "Update"
                ):

                    supabase.table(
                    "tickets"
                    ).update({

                    "status":status,
                    "assigned_to":assign,
                    "remarks":remarks

                    }).eq(
                    "ticket_number",
                    tid
                    ).execute()

                    st.success(
                    "Updated"
                    )

        else:

            with st.form("userupdate"):

                status=st.selectbox(
                "Status",
                [
                "Open",
                "In Progress",
                "Resolved"
                ])

                remarks=st.text_area(
                "Remarks"
                )

                if st.form_submit_button(
                "Update"
                ):

                    supabase.table(
                    "tickets"
                    ).update({

                    "status":status,
                    "remarks":remarks

                    }).eq(
                    "ticket_number",
                    tid
                    ).execute()

                    st.success(
                    "Updated"
                    )


##########################################
# DELETE ADMIN
##########################################

    elif choice=="Delete Ticket":

        st.title("Delete Ticket")

        df=get_data()

        options={
        f'{r["ticket_number"]}-{r["summary"]}':
        r["ticket_number"]
        for _,r in df.iterrows()
        }

        selected=st.selectbox(
        "Select Ticket",
        list(options.keys())
        )

        tid=options[selected]

        if st.button(
        "Delete"
        ):

            supabase.table(
            "tickets"
            ).delete().eq(
            "ticket_number",
            tid
            ).execute()

            st.success(
            "Deleted"
            )


##########################################
# REPORTS ADMIN
##########################################

    elif choice=="Reports":

        st.title("Reports")

        df=get_data()

        st.dataframe(df)

        st.metric(
        "Total Tickets",
        len(df)
        )


##########################################
# SETTINGS ADMIN
##########################################

    elif choice=="Settings":

        st.title(
        "Create New User"
        )

        with st.form(
        "newuser"
        ):

            uname=st.text_input(
            "Username"
            )

            pwd=st.text_input(
            "Password",
            type="password"
            )

            create=st.checkbox(
            "Create Ticket",
            True
            )

            update=st.checkbox(
            "Update Ticket",
            True
            )

            admin=st.checkbox(
            "Admin"
            )

            if st.form_submit_button(
            "Create User"
            ):

                supabase.table(
                "users"
                ).insert({

                "username":uname,
                "password":pwd,
                "can_create_ticket":
                    create if not admin else True,

                "can_update_ticket":
                    update if not admin else True,

                "is_admin":admin

                }).execute()

                st.success(
                "User Created"
                )


##########################################
# LOGOUT
##########################################

    elif choice=="Logout":
        logout()
