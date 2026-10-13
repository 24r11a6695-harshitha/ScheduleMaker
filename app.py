import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
from csp_solver import StudySchedulerCSP

st.set_page_config(page_title="Smart Schedule Maker", layout="wide")

# Initialize authentication state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- NATIVE STREAMLIT LOGIN / REGISTER PAGE ---
if not st.session_state.authenticated:
    st.title("📅 Welcome to Schedule Maker")
    st.caption("Please login or create an account to continue")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])
        
        # LOGIN TAB
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username or Email")
                password = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Login", type="primary", use_container_width=True)
                
                if submit_login:
                    if username.strip():
                        st.session_state.authenticated = True
                        st.session_state.username = username.strip()
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Please enter a valid username or email.")

        # REGISTER TAB
        with tab_register:
            with st.form("register_form"):
                reg_username = st.text_input("Username or Email", key="reg_user")
                reg_password = st.text_input("Password", type="password", key="reg_pass")
                reg_confirm = st.text_input("Confirm Password", type="password", key="reg_conf")
                submit_register = st.form_submit_button("Register", type="primary", use_container_width=True)
                
                if submit_register:
                    if not reg_username.strip():
                        st.error("Please enter a username.")
                    elif reg_password != reg_confirm:
                        st.error("Passwords do not match!")
                    else:
                        st.session_state.authenticated = True
                        st.session_state.username = reg_username.strip()
                        st.success("Account created successfully!")
                        st.rerun()

    st.stop()

# --- PRESET INITIALIZATION ---
if "topics_list" not in st.session_state:
    st.session_state.topics_list = [
        {"topic": "Team Sync & Planning", "hours": 2, "time": "09:30"},
        {"topic": "Project Development & Coding", "hours": 4, "time": "11:30"},
        {"topic": "Review & Testing", "hours": 2, "time": "15:00"}
    ]

if "schedule_result" not in st.session_state:
    st.session_state.schedule_result = None

if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today().strftime("%Y-%m-%d")

# --- HEADER BAR ---
header_col1, header_col2 = st.columns([3, 1.5])
with header_col1:
    st.title("📅 OptiPlan Schedule Maker")
    st.caption("Plan your tasks, projects, and events efficiently.")

with header_col2:
    st.write("")
    st.markdown(f"👤 **{st.session_state.username}**")
    
    col_h_btn1, col_h_btn2 = st.columns(2)
    with col_h_btn1:
        if st.button("🔔 Notifications"):
            st.toast("Notifications enabled!", icon="🔔")
    with col_h_btn2:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.rerun()

st.markdown("---")

# --- CONSTRAINTS FORM ---
st.subheader("Event Planning & Time Constraints")

c_col1, c_col2, c_col3 = st.columns(3)
with c_col1:
    start_date = st.date_input("Start Date", value=date.today())
with c_col2:
    days_to_exam = st.number_input("Total Days", min_value=1, max_value=30, value=7)
with c_col3:
    max_hrs_per_day = st.number_input("Max Hours / Day", min_value=1, max_value=12, value=6)

st.write("")

h_col1, h_col2, h_col3, h_col4 = st.columns([5, 2, 2, 0.8])
h_col1.caption("**EVENT NAME**")
h_col2.caption("**HOURS**")
h_col3.caption("**START TIME**")
h_col4.caption("")

updated_topics = []
to_delete = None

for idx, item in enumerate(st.session_state.topics_list):
    r_col1, r_col2, r_col3, r_col4 = st.columns([5, 2, 2, 0.8])
    
    top = r_col1.text_input(f"top_{idx}", value=item["topic"], label_visibility="collapsed")
    hrs = r_col2.number_input(f"hrs_{idx}", value=item["hours"], min_value=1, max_value=10, label_visibility="collapsed")
    tm = r_col3.text_input(f"tm_{idx}", value=item["time"], label_visibility="collapsed")
    
    if r_col4.button("🗑", key=f"del_{idx}"):
        to_delete = idx
        
    updated_topics.append({"topic": top, "hours": hrs, "time": tm})

if to_delete is not None:
    st.session_state.topics_list.pop(to_delete)
    st.rerun()

st.session_state.topics_list = updated_topics

b_col1, b_col2, _ = st.columns([1.5, 2, 4])

with b_col1:
    if st.button("➕ Add Event"):
        st.session_state.topics_list.append({"topic": "", "hours": 1, "time": "09:00"})
        st.rerun()

with b_col2:
    if st.button("🚀 Generate Schedule", type="primary"):
        available_days = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days_to_exam)]
        
        solver = StudySchedulerCSP(
            topics=st.session_state.topics_list, 
            available_days=available_days, 
            max_hours_per_day=max_hrs_per_day,
            max_hrs_per_subject_per_day=3
        )
        assignment = solver.backtrack({})
        
        if assignment is not None:
            st.session_state.schedule_result = {
                "assignment": assignment,
                "days": available_days,
                "blocks": solver.blocks
            }
            st.success("Schedule generated successfully!")
        else:
            st.error("Cannot fit all events under these constraints! Increase total days or max hours per day.")

# --- CALENDAR VIEW ---
st.markdown("---")
col_cal, col_inspector = st.columns([2.2, 1])

with col_cal:
    st.subheader("Schedule Calendar")
    
    if st.session_state.schedule_result:
        days = st.session_state.schedule_result["days"]
        assignment = st.session_state.schedule_result["assignment"]
        blocks = st.session_state.schedule_result["blocks"]
        
        daily_hours = {}
        for day_str in days:
            daily_hours[day_str] = sum(
                1 for idx, assigned_day in assignment.items() if assigned_day == day_str
            )
        
        selected_day = st.radio("Select Calendar Date:", days, horizontal=True)
        st.session_state.selected_date = selected_day
        
        weekdays = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        grid_cols = st.columns(7)
        
        for col, day_name in zip(grid_cols, weekdays):
            col.markdown(f"<div style='text-align: center; font-size: 12px; font-weight: bold; margin-bottom: 8px;'>{day_name}</div>", unsafe_allow_html=True)
            
        for day_str in days:
            dt = datetime.strptime(day_str, "%Y-%m-%d")
            weekday_idx = dt.weekday()
            day_num = dt.day
            month_str = dt.strftime("%b")
            hrs_total = daily_hours[day_str]
            
            is_active = (day_str == st.session_state.selected_date)
            border_style = "2px solid #FF4B4B" if is_active else "1px solid #444444"
            
            with grid_cols[weekday_idx]:
                st.markdown(f"""
                <div style="border: {border_style}; border-radius: 8px; padding: 8px; height: 85px; font-family: sans-serif; margin-bottom: 8px;">
                    <div style="font-size: 14px; font-weight: bold; color: #FF4B4B;">{day_num}</div>
                    <div style="font-size: 10px; opacity: 0.7;">{month_str}</div>
                    <div style="font-size: 11px; font-weight: bold; margin-top: 10px;">{f'{hrs_total}h' if hrs_total > 0 else ''}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Click 'Generate Schedule' above to populate the calendar view.")

with col_inspector:
    st.subheader("Event Inspector")
    
    selected_date_str = st.session_state.selected_date
    if selected_date_str:
        dt = datetime.strptime(selected_date_str, "%Y-%m-%d")
        formatted_header = dt.strftime("%A, %d %B")
        st.markdown(f"#### {formatted_header}")
    
    if st.session_state.schedule_result:
        assignment = st.session_state.schedule_result["assignment"]
        blocks = st.session_state.schedule_result["blocks"]
        
        day_blocks = [
            blocks[idx] 
            for idx, assigned_day in assignment.items() 
            if assigned_day == selected_date_str
        ]
        
        if day_blocks:
            total_hrs = len(day_blocks)
            for block in day_blocks:
                st.markdown(f"""
                <div style="border-radius: 8px; padding: 10px; margin-bottom: 8px; border-left: 4px solid #FF4B4B; background-color: rgba(255, 75, 75, 0.1);">
                    <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: bold;">
                        <span>TASK</span>
                        <span>🔔 {block['time']}</span>
                    </div>
                    <div style="font-size: 13px; font-weight: bold; margin-top: 2px;">
                        {block['topic']}
                    </div>
                    <div style="font-size: 11px; opacity: 0.7;">
                        1h · part {block['part']} of {block['total_parts']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"<div style='text-align: right; font-weight: bold; font-size: 13px; margin-top: 8px;'>Total: {total_hrs}h</div>", unsafe_allow_html=True)
        else:
            st.write("No events scheduled for this date.")
    else:
        st.write("Select a date on the calendar to view scheduled events.")