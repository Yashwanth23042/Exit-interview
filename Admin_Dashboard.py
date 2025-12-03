# # import streamlit as st
# # import requests
# # import pandas as pd
# # from datetime import datetime, date
# # import os
# # from dotenv import load_dotenv

# # load_dotenv()

# # # API Configuration
# # API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# # # Page Configuration
# # st.set_page_config(
# #     page_title="HR Exit Interview Dashboard",
# #     page_icon="🏢",
# #     layout="wide"
# # )

# # # Custom CSS
# # st.markdown("""
# # <style>
# #     .main-header {
# #         font-size: 2.5rem;
# #         font-weight: bold;
# #         color: #1f77b4;
# #     }
# #     .metric-card {
# #         background-color: #f0f2f6;
# #         padding: 20px;
# #         border-radius: 10px;
# #         text-align: center;
# #     }
# # </style>
# # """, unsafe_allow_html=True)

# # # ==================== API FUNCTIONS ====================

# # def add_employee(name, email, department, last_working_date):
# #     """Add new employee via API"""
# #     try:
# #         data = {
# #             "name": name,
# #             "email": email,
# #             "department": department,
# #             "last_working_date": str(last_working_date)
# #         }
# #         response = requests.post(f"{API_BASE_URL}/employees", json=data)
# #         response.raise_for_status()
# #         return response.json(), None
# #     except requests.exceptions.RequestException as e:
# #         return None, str(e)

# # def get_employees():
# #     """Get all employees"""
# #     try:
# #         response = requests.get(f"{API_BASE_URL}/employees")
# #         response.raise_for_status()
# #         return response.json(), None
# #     except requests.exceptions.RequestException as e:
# #         return None, str(e)

# # def get_statistics():
# #     """Get dashboard statistics"""
# #     try:
# #         response = requests.get(f"{API_BASE_URL}/stats")
# #         response.raise_for_status()
# #         return response.json(), None
# #     except requests.exceptions.RequestException as e:
# #         return None, str(e)

# # def resend_email(employee_id):
# #     """Resend interview email"""
# #     try:
# #         response = requests.post(f"{API_BASE_URL}/employees/{employee_id}/resend-email")
# #         response.raise_for_status()
# #         return response.json(), None
# #     except requests.exceptions.RequestException as e:
# #         return None, str(e)

# # def get_interview_responses(interview_id):
# #     """Get interview responses"""
# #     try:
# #         response = requests.get(f"{API_BASE_URL}/interviews/{interview_id}/responses")
# #         response.raise_for_status()
# #         return response.json(), None
# #     except requests.exceptions.RequestException as e:
# #         return None, str(e)

# # # ==================== SIDEBAR NAVIGATION ====================

# # st.sidebar.title("🏢 HR Dashboard")
# # st.sidebar.markdown("---")

# # page = st.sidebar.selectbox(
# #     "Navigation",
# #     ["📊 Dashboard", "➕ Add Employee", "👥 View Employees", "📝 View Responses"]
# # )

# # st.sidebar.markdown("---")
# # st.sidebar.info("🤖 AI Exit Interview System\nPowered by Nova (AWS Bedrock)")

# # # ==================== PAGE 1: DASHBOARD ====================

# # if page == "📊 Dashboard":
# #     st.markdown('<p class="main-header">📊 Exit Interview Dashboard</p>', unsafe_allow_html=True)
# #     st.markdown("---")
    
# #     # Get statistics
# #     stats, error = get_statistics()
    
# #     if error:
# #         st.error(f"⚠️ Error connecting to backend: {error}")
# #         st.info("Make sure backend is running: `python backend/main.py`")
# #     else:
# #         # Display metrics
# #         col1, col2, col3, col4 = st.columns(4)
        
# #         with col1:
# #             st.metric(
# #                 label="Total Resignations",
# #                 value=stats['total_resignations'],
# #                 delta=None
# #             )
        
# #         with col2:
# #             st.metric(
# #                 label="Completed Interviews",
# #                 value=stats['completed_interviews'],
# #                 delta=None
# #             )
        
# #         with col3:
# #             st.metric(
# #                 label="Pending Interviews",
# #                 value=stats['pending_interviews'],
# #                 delta=None
# #             )
        
# #         with col4:
# #             st.metric(
# #                 label="Completion Rate",
# #                 value=f"{stats['completion_rate']:.1f}%",
# #                 delta=None
# #             )
        
# #         st.markdown("---")
        
# #         # Recent employees
# #         st.subheader("📋 Recent Exit Interviews")
        
# #         employees, error = get_employees()
        
# #         if error:
# #             st.error(f"Error loading employees: {error}")
# #         elif not employees:
# #             st.info("No employees added yet. Use 'Add Employee' to get started.")
# #         else:
# #             # Create dataframe
# #             df_data = []
# #             for emp in employees:
# #                 interview = emp.get('interview', {})
# #                 df_data.append({
# #                     'ID': emp['id'],
# #                     'Name': emp['name'],
# #                     'Email': emp['email'],
# #                     'Department': emp['department'],
# #                     'Last Working Date': emp['last_working_date'],
# #                     'Status': '✅ Completed' if interview and interview.get('completed') else '⏳ Pending',
# #                     'Date Added': emp['created_at'][:10] if emp.get('created_at') else 'N/A'
# #                 })
            
# #             df = pd.DataFrame(df_data)
# #             st.dataframe(df, use_container_width=True, hide_index=True)

# # # ==================== PAGE 2: ADD EMPLOYEE ====================

# # elif page == "➕ Add Employee":
# #     st.markdown('<p class="main-header">➕ Add New Employee</p>', unsafe_allow_html=True)
# #     st.markdown("---")
    
# #     st.info("💡 After adding, an AI exit interview email will be sent automatically with Nova!")
    
# #     with st.form("add_employee_form"):
# #         col1, col2 = st.columns(2)
        
# #         with col1:
# #             name = st.text_input("Employee Name *", placeholder="e.g., Ravi Kumar")
# #             email = st.text_input("Email Address *", placeholder="e.g., ravi@company.com")
        
# #         with col2:
# #             department = st.selectbox(
# #                 "Department *",
# #                 ["Engineering", "HR", "Sales", "Marketing", "Finance", "Operations", "IT", "Customer Support"]
# #             )
# #             last_working_date = st.date_input(
# #                 "Last Working Date *",
# #                 min_value=date.today()
# #             )
        
# #         st.markdown("---")
# #         submitted = st.form_submit_button("➕ Add Employee & Send AI Interview Email", use_container_width=True)
        
# #         if submitted:
# #             # Validation
# #             if not name or not email:
# #                 st.error("❌ Please fill all required fields!")
# #             elif "@" not in email:
# #                 st.error("❌ Please enter a valid email address!")
# #             else:
# #                 with st.spinner("Adding employee and sending AI interview email..."):
# #                     result, error = add_employee(name, email, department, last_working_date)
                    
# #                     if error:
# #                         st.error(f"❌ Error: {error}")
# #                         if "already exists" in str(error):
# #                             st.warning("This email is already registered in the system.")
# #                     else:
# #                         st.success(f"✅ Employee added successfully!")
# #                         st.success(f"📧 AI Interview email sent to {email}")
# #                         st.balloons()
                        
# #                         # Show details
# #                         st.info(f"""
# #                         **Employee Details:**
# #                         - Name: {name}
# #                         - Email: {email}
# #                         - Department: {department}
# #                         - Last Working Date: {last_working_date}
# #                         - Interview Type: 🤖 AI Conversation with Nova
# #                         """)

# # # ==================== PAGE 3: VIEW EMPLOYEES ====================

# # elif page == "👥 View Employees":
# #     st.markdown('<p class="main-header">👥 All Employees</p>', unsafe_allow_html=True)
# #     st.markdown("---")
    
# #     # Filters
# #     col1, col2, col3 = st.columns([2, 2, 1])
    
# #     with col1:
# #         status_filter = st.selectbox("Filter by Status", ["All", "Resigned", "Completed"])
    
# #     with col3:
# #         if st.button("🔄 Refresh", use_container_width=True):
# #             st.rerun()
    
# #     st.markdown("---")
    
# #     # Get employees
# #     employees, error = get_employees()
    
# #     if error:
# #         st.error(f"Error: {error}")
# #     elif not employees:
# #         st.info("No employees found.")
# #     else:
# #         # Apply filter
# #         if status_filter != "All":
# #             employees = [emp for emp in employees if emp['status'] == status_filter]
        
# #         # Display as cards
# #         for emp in employees:
# #             interview = emp.get('interview', {})
# #             is_completed = interview and interview.get('completed', False)
            
# #             with st.expander(f"🤖 {'✅' if is_completed else '⏳'} {emp['name']} - {emp['department']}", expanded=False):
# #                 col1, col2 = st.columns(2)
                
# #                 with col1:
# #                     st.write(f"**Email:** {emp['email']}")
# #                     st.write(f"**Department:** {emp['department']}")
# #                     st.write(f"**Last Working Date:** {emp['last_working_date']}")
                
# #                 with col2:
# #                     st.write(f"**Status:** {emp['status']}")
# #                     st.write(f"**Added On:** {emp['created_at'][:10]}")
# #                     if interview:
# #                         st.write(f"**Interview:** {'✅ Completed' if is_completed else '⏳ Pending'}")
                
# #                 # Action buttons
# #                 col_btn1, col_btn2, col_btn3 = st.columns(3)
                
# #                 with col_btn1:
# #                     if not is_completed:
# #                         if st.button(f"📧 Resend Email", key=f"resend_{emp['id']}"):
# #                             with st.spinner("Sending email..."):
# #                                 result, error = resend_email(emp['id'])
# #                                 if error:
# #                                     st.error(f"Error: {error}")
# #                                 else:
# #                                     st.success("✅ Email sent!")
                
# #                 with col_btn2:
# #                     if is_completed and interview:
# #                         if st.button(f"👁️ View Responses", key=f"view_{emp['id']}"):
# #                             st.session_state['view_interview_id'] = interview['id']
# #                             st.session_state['view_employee_name'] = emp['name']

# # # ==================== PAGE 4: VIEW RESPONSES ====================

# # elif page == "📝 View Responses":
# #     st.markdown('<p class="main-header">📝 Interview Responses</p>', unsafe_allow_html=True)
# #     st.markdown("---")
    
# #     # Get all employees
# #     employees, error = get_employees()
    
# #     if error:
# #         st.error(f"Error: {error}")
# #     elif not employees:
# #         st.info("No employees found.")
# #     else:
# #         # Filter only completed interviews
# #         completed = [emp for emp in employees if emp.get('interview', {}).get('completed')]
        
# #         if not completed:
# #             st.info("No completed interviews yet.")
# #         else:
# #             # Select employee
# #             employee_options = {f"{emp['name']} ({emp['email']})": emp for emp in completed}
# #             selected_name = st.selectbox("Select Employee", list(employee_options.keys()))
            
# #             if selected_name:
# #                 selected_emp = employee_options[selected_name]
# #                 interview = selected_emp['interview']
                
# #                 st.markdown("---")
# #                 st.subheader(f"📋 AI Interview Responses - {selected_emp['name']}")
                
# #                 col1, col2, col3 = st.columns(3)
# #                 with col1:
# #                     st.write(f"**Department:** {selected_emp['department']}")
# #                 with col2:
# #                     st.write(f"**Email:** {selected_emp['email']}")
# #                 with col3:
# #                     st.write(f"**Completed On:** {interview['created_at'][:10]}")
                
# #                 st.markdown("---")
                
# #                 # Get responses
# #                 responses, error = get_interview_responses(interview['id'])
                
# #                 if error:
# #                     st.error(f"Error loading responses: {error}")
# #                 elif not responses:
# #                     st.warning("No responses found.")
# #                 else:
# #                     # Display responses
# #                     for i, response in enumerate(responses, 1):
# #                         if "Transcript" in response['question']:
# #                             # Show full transcript in expandable section
# #                             with st.expander("📜 View Full AI Conversation Transcript"):
# #                                 st.text_area(
# #                                     "Full Conversation",
# #                                     response['answer'],
# #                                     height=400,
# #                                     label_visibility="collapsed"
# #                                 )
# #                         else:
# #                             st.markdown(f"**Q{i}: {response['question']}**")
# #                             st.info(f"📝 {response['answer']}")
# #                             st.markdown("")

# # # ==================== FOOTER ====================

# # st.sidebar.markdown("---")
# # st.sidebar.markdown("**System Status:**")
# # st.sidebar.success("✅ Backend Connected")
# # st.sidebar.caption("Version 2.1.0 - AI Powered")



# import streamlit as st
# import requests
# import pandas as pd
# from datetime import datetime, date
# import os
# from dotenv import load_dotenv
# import json

# load_dotenv()

# API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# st.set_page_config(
#     page_title="HR Exit Interview Dashboard",
#     page_icon="🏢",
#     layout="wide"
# )

# # Custom CSS
# st.markdown("""
# <style>
#     .main-header {
#         font-size: 2.5rem;
#         font-weight: bold;
#         color: #1f77b4;
#     }
# </style>
# """, unsafe_allow_html=True)

# # ==================== API FUNCTIONS ====================

# def add_employee(name, email, department, last_working_date, questions):
#     """Add new employee with custom questions"""
#     try:
#         data = {
#             "name": name,
#             "email": email,
#             "department": department,
#             "last_working_date": str(last_working_date),
#             "questions": questions
#         }
#         response = requests.post(f"{API_BASE_URL}/employees", json=data)
#         response.raise_for_status()
#         return response.json(), None
#     except requests.exceptions.RequestException as e:
#         return None, str(e)

# def get_employees():
#     """Get all employees"""
#     try:
#         response = requests.get(f"{API_BASE_URL}/employees")
#         response.raise_for_status()
#         return response.json(), None
#     except requests.exceptions.RequestException as e:
#         return None, str(e)

# def get_statistics():
#     """Get dashboard statistics"""
#     try:
#         response = requests.get(f"{API_BASE_URL}/stats")
#         response.raise_for_status()
#         return response.json(), None
#     except requests.exceptions.RequestException as e:
#         return None, str(e)

# def get_interview_responses(interview_id):
#     """Get interview responses"""
#     try:
#         response = requests.get(f"{API_BASE_URL}/interviews/{interview_id}/responses")
#         response.raise_for_status()
#         return response.json(), None
#     except requests.exceptions.RequestException as e:
#         return None, str(e)

# # ==================== SIDEBAR ====================

# st.sidebar.title("🏢 HR Dashboard")
# st.sidebar.markdown("---")

# page = st.sidebar.selectbox(
#     "Navigation",
#     ["📊 Dashboard", "➕ Add Employee", "👥 View Employees", "📝 View Responses"]
# )

# st.sidebar.markdown("---")
# st.sidebar.info("🎙️ Voice Exit Interview System\nPowered by Nova Sonic (AWS)")

# # ==================== PAGE 1: DASHBOARD ====================

# if page == "📊 Dashboard":
#     st.markdown('<p class="main-header">📊 Exit Interview Dashboard</p>', unsafe_allow_html=True)
#     st.markdown("---")
    
#     stats, error = get_statistics()
    
#     if error:
#         st.error(f"⚠️ Error: {error}")
#         st.info("Make sure backend is running: `python backend/main.py`")
#     else:
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             st.metric("Total Resignations", stats['total_resignations'])
#         with col2:
#             st.metric("Completed Interviews", stats['completed_interviews'])
#         with col3:
#             st.metric("Pending Interviews", stats['pending_interviews'])
#         with col4:
#             st.metric("Completion Rate", f"{stats['completion_rate']:.1f}%")
        
#         st.markdown("---")
        
#         st.subheader("📋 Recent Exit Interviews")
        
#         employees, error = get_employees()
        
#         if error:
#             st.error(f"Error: {error}")
#         elif not employees:
#             st.info("No employees added yet.")
#         else:
#             df_data = []
#             for emp in employees:
#                 interview = emp.get('interview', {})
#                 df_data.append({
#                     'ID': emp['id'],
#                     'Name': emp['name'],
#                     'Email': emp['email'],
#                     'Department': emp['department'],
#                     'Last Working Date': emp['last_working_date'],
#                     'Status': '✅ Completed' if interview and interview.get('completed') else '⏳ Pending',
#                     'Date Added': emp['created_at'][:10] if emp.get('created_at') else 'N/A'
#                 })
            
#             df = pd.DataFrame(df_data)
#             st.dataframe(df, use_container_width=True, hide_index=True)

# # ==================== PAGE 2: ADD EMPLOYEE ====================

# elif page == "➕ Add Employee":
#     st.markdown('<p class="main-header">➕ Add New Employee</p>', unsafe_allow_html=True)
#     st.markdown("---")
    
#     st.info("💡 Upload custom questions for Nova to ask during the voice interview!")
    
#     # Initialize session state for questions
#     if 'custom_questions' not in st.session_state:
#         st.session_state.custom_questions = [
#             "What was your primary reason for leaving?",
#             "How would you rate your overall experience with the company on a scale of 1 to 5?",
#             "How was your relationship with your manager?",
#             "Did you feel valued and recognized in your role?",
#             "Would you recommend our company to others? Why or why not?"
#         ]
    
#     # Question Management Section
#     st.subheader("📝 Interview Questions")
#     st.markdown("Nova will ask these questions during the voice interview:")
    
#     # Display and edit questions
#     questions_to_remove = []
#     for i, question in enumerate(st.session_state.custom_questions):
#         col1, col2 = st.columns([4, 1])
#         with col1:
#             new_question = st.text_input(
#                 f"Question {i+1}",
#                 value=question,
#                 key=f"q_{i}",
#                 label_visibility="collapsed"
#             )
#             st.session_state.custom_questions[i] = new_question
#         with col2:
#             if st.button("🗑️", key=f"del_{i}"):
#                 questions_to_remove.append(i)
    
#     # Remove questions
#     for idx in sorted(questions_to_remove, reverse=True):
#         st.session_state.custom_questions.pop(idx)
    
#     # Add new question
#     col1, col2 = st.columns([3, 1])
#     with col1:
#         new_question_input = st.text_input("Add new question", key="new_question_input")
#     with col2:
#         st.write("")  # Spacing
#         st.write("")  # Spacing
#         if st.button("➕ Add Question", use_container_width=True):
#             if new_question_input.strip():
#                 st.session_state.custom_questions.append(new_question_input.strip())
#                 st.rerun()
    
#     # Upload questions from file
#     st.markdown("---")
#     st.markdown("**Or upload questions from a file:**")
    
#     uploaded_file = st.file_uploader(
#         "Upload questions (one per line in .txt file)",
#         type=['txt'],
#         help="Upload a text file with one question per line"
#     )
    
#     if uploaded_file:
#         content = uploaded_file.read().decode('utf-8')
#         file_questions = [q.strip() for q in content.split('\n') if q.strip()]
#         st.session_state.custom_questions = file_questions
#         st.success(f"✅ Loaded {len(file_questions)} questions from file!")
#         st.rerun()
    
#     st.markdown("---")
    
#     # Employee Form
#     st.subheader("👤 Employee Details")
    
#     with st.form("add_employee_form"):
#         col1, col2 = st.columns(2)
        
#         with col1:
#             name = st.text_input("Employee Name *", placeholder="e.g., Ravi Kumar")
#             email = st.text_input("Email Address *", placeholder="e.g., ravi@company.com")
        
#         with col2:
#             department = st.selectbox(
#                 "Department *",
#                 ["Engineering", "HR", "Sales", "Marketing", "Finance", "Operations", "IT", "Customer Support"]
#             )
#             last_working_date = st.date_input(
#                 "Last Working Date *",
#                 min_value=date.today()
#             )
        
#         st.markdown("---")
        
#         # Preview questions
#         with st.expander("📋 Preview Questions Nova Will Ask", expanded=False):
#             for i, q in enumerate(st.session_state.custom_questions, 1):
#                 st.markdown(f"{i}. {q}")
        
#         submitted = st.form_submit_button(
#             "➕ Add Employee & Send Voice Interview Email",
#             use_container_width=True
#         )
        
#         if submitted:
#             if not name or not email:
#                 st.error("❌ Please fill all required fields!")
#             elif "@" not in email:
#                 st.error("❌ Please enter a valid email!")
#             elif not st.session_state.custom_questions:
#                 st.error("❌ Please add at least one question!")
#             else:
#                 with st.spinner("Adding employee and sending voice interview email..."):
#                     result, error = add_employee(
#                         name, email, department,
#                         last_working_date,
#                         st.session_state.custom_questions
#                     )
                    
#                     if error:
#                         st.error(f"❌ Error: {error}")
#                     else:
#                         st.success(f"✅ Employee added successfully!")
#                         st.success(f"📧 Voice interview email sent to {email}")
#                         st.balloons()
                        
#                         st.info(f"""
#                         **Employee Details:**
#                         - Name: {name}
#                         - Email: {email}
#                         - Department: {department}
#                         - Last Working Date: {last_working_date}
#                         - Interview Type: 🎙️ Voice with Nova Sonic
#                         - Questions: {len(st.session_state.custom_questions)} custom questions
#                         """)

# # ==================== PAGE 3: VIEW EMPLOYEES ====================

# elif page == "👥 View Employees":
#     st.markdown('<p class="main-header">👥 All Employees</p>', unsafe_allow_html=True)
#     st.markdown("---")
    
#     col1, col2, col3 = st.columns([2, 2, 1])
    
#     with col1:
#         status_filter = st.selectbox("Filter by Status", ["All", "Resigned", "Completed"])
    
#     with col3:
#         if st.button("🔄 Refresh", use_container_width=True):
#             st.rerun()
    
#     st.markdown("---")
    
#     employees, error = get_employees()
    
#     if error:
#         st.error(f"Error: {error}")
#     elif not employees:
#         st.info("No employees found.")
#     else:
#         if status_filter != "All":
#             employees = [emp for emp in employees if emp['status'] == status_filter]
        
#         for emp in employees:
#             interview = emp.get('interview', {})
#             is_completed = interview and interview.get('completed', False)
            
#             with st.expander(
#                 f"🎙️ {'✅' if is_completed else '⏳'} {emp['name']} - {emp['department']}",
#                 expanded=False
#             ):
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     st.write(f"**Email:** {emp['email']}")
#                     st.write(f"**Department:** {emp['department']}")
#                     st.write(f"**Last Working Date:** {emp['last_working_date']}")
                
#                 with col2:
#                     st.write(f"**Status:** {emp['status']}")
#                     st.write(f"**Added On:** {emp['created_at'][:10]}")
#                     if interview:
#                         st.write(f"**Interview:** {'✅ Completed' if is_completed else '⏳ Pending'}")
                
#                 if is_completed and interview:
#                     if st.button(f"👁️ View Voice Responses", key=f"view_{emp['id']}"):
#                         st.session_state['view_interview_id'] = interview['id']
#                         st.session_state['view_employee_name'] = emp['name']

# # ==================== PAGE 4: VIEW RESPONSES ====================

# elif page == "📝 View Responses":
#     st.markdown('<p class="main-header">📝 Voice Interview Responses</p>', unsafe_allow_html=True)
#     st.markdown("---")
    
#     employees, error = get_employees()
    
#     if error:
#         st.error(f"Error: {error}")
#     elif not employees:
#         st.info("No employees found.")
#     else:
#         completed = [emp for emp in employees if emp.get('interview', {}).get('completed')]
        
#         if not completed:
#             st.info("No completed interviews yet.")
#         else:
#             employee_options = {f"{emp['name']} ({emp['email']})": emp for emp in completed}
#             selected_name = st.selectbox("Select Employee", list(employee_options.keys()))
            
#             if selected_name:
#                 selected_emp = employee_options[selected_name]
#                 interview = selected_emp['interview']
                
#                 st.markdown("---")
#                 st.subheader(f"🎙️ Voice Interview Responses - {selected_emp['name']}")
                
#                 col1, col2, col3 = st.columns(3)
#                 with col1:
#                     st.write(f"**Department:** {selected_emp['department']}")
#                 with col2:
#                     st.write(f"**Email:** {selected_emp['email']}")
#                 with col3:
#                     st.write(f"**Completed On:** {interview['created_at'][:10]}")
                
#                 st.markdown("---")
                
#                 responses, error = get_interview_responses(interview['id'])
                
#                 if error:
#                     st.error(f"Error: {error}")
#                 elif not responses:
#                     st.warning("No responses found.")
#                 else:
#                     for i, response in enumerate(responses, 1):
#                         st.markdown(f"**Q{i}: {response['question']}**")
#                         st.info(f"📝 {response['answer']}")
                        
#                         if response.get('audio_url'):
#                             st.audio(response['audio_url'])
                        
#                         st.markdown("")

# # ==================== FOOTER ====================

# st.sidebar.markdown("---")
# st.sidebar.markdown("**System Status:**")
# st.sidebar.success("✅ Backend Connected")
# st.sidebar.caption("Version 3.0.0 - Voice AI Powered")


import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import os
from dotenv import load_dotenv
import json
import PyPDF2
from io import BytesIO

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

st.set_page_config(
    page_title="HR Exit Interview Dashboard",
    page_icon="🏢",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .question-card {
        background: #f0f2f6;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# ==================== API FUNCTIONS ====================

def add_employee(name, email, department, last_working_date, questions):
    """Add new employee with custom questions"""
    try:
        data = {
            "name": name,
            "email": email,
            "department": department,
            "last_working_date": str(last_working_date),
            "questions": questions
        }
        response = requests.post(f"{API_BASE_URL}/employees", json=data)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, str(e)

def get_employees():
    """Get all employees"""
    try:
        response = requests.get(f"{API_BASE_URL}/employees")
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, str(e)
    
    

def get_statistics():
    """Get dashboard statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, str(e)

def get_interview_responses(interview_id):
    """Get interview responses"""
    try:
        response = requests.get(f"{API_BASE_URL}/interviews/{interview_id}/responses")
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, str(e)

# ==================== QUESTION PROCESSING ====================

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return None

def parse_questions_from_text(text):
    """Parse questions from text content"""
    lines = text.strip().split('\n')
    questions = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Remove common numbering patterns (1., Q1:, 1), etc.)
        cleaned = line
        for pattern in ['Q)', 'Q.', 'Q:', 'q)']:
            if cleaned.startswith(pattern):
                cleaned = cleaned[len(pattern):].strip()
                break
        
        # Handle numbered patterns (1., 1), 1:, etc.)
        for i in range(10):
            for sep in ['.', ')', ':']:
                prefix = f"{i}{sep} "
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
                    break
        
        # Only add if it's a question (ends with ?) or substantial text
        if cleaned and (cleaned.endswith('?') or len(cleaned) > 10):
            questions.append(cleaned)
    
    return questions

def load_questions_from_file(uploaded_file):
    """Load questions from various file types"""
    try:
        if uploaded_file.type == "application/pdf":
            text = extract_text_from_pdf(uploaded_file)
            if text:
                return parse_questions_from_text(text)
        
        elif uploaded_file.type == "text/plain":
            content = uploaded_file.read().decode('utf-8')
            return parse_questions_from_text(content)
        
        elif uploaded_file.type in ["application/vnd.ms-excel", 
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            import pandas as pd
            df = pd.read_excel(uploaded_file)
            questions = []
            for col in df.columns:
                questions.extend(df[col].dropna().astype(str).tolist())
            return [q.strip() for q in questions if q.strip()]
        
        return None
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None

# ==================== SIDEBAR ====================

st.sidebar.title("🏢 HR Dashboard")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Navigation",
    ["📊 Dashboard", "➕ Add Employee", "👥 View Employees", "📝 View Responses"]
)

st.sidebar.markdown("---")
st.sidebar.info("🎙️ Voice Exit Interview System\nPowered by Nova Sonic (AWS)")

# ==================== PAGE 1: DASHBOARD ====================

if page == "📊 Dashboard":
    st.markdown('<p class="main-header">📊 Exit Interview Dashboard</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    stats, error = get_statistics()
    
    if error:
        st.error(f"⚠️ Error: {error}")
        st.info("Make sure backend is running: `python backend/main.py`")
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Resignations", stats['total_resignations'])
        with col2:
            st.metric("Completed Interviews", stats['completed_interviews'])
        with col3:
            st.metric("Pending Interviews", stats['pending_interviews'])
        with col4:
            st.metric("Completion Rate", f"{stats['completion_rate']:.1f}%")
        
        st.markdown("---")
        
        st.subheader("📋 Recent Exit Interviews")
        
        employees, error = get_employees()
        
        if error:
            st.error(f"Error: {error}")
        elif not employees:
            st.info("No employees added yet.")
        else:
            df_data = []
            for emp in employees:
                interview = emp.get('interview', {})
                df_data.append({
                    'ID': emp['id'],
                    'Name': emp['name'],
                    'Email': emp['email'],
                    'Department': emp['department'],
                    'Last Working Date': emp['last_working_date'],
                    'Status': '✅ Completed' if interview and interview.get('completed') else '⏳ Pending',
                    'Date Added': emp['created_at'][:10] if emp.get('created_at') else 'N/A'
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

# ==================== PAGE 2: ADD EMPLOYEE ====================

elif page == "➕ Add Employee":
    st.markdown('<p class="main-header">➕ Add New Employee</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.info("💡 HR can upload a document or manually add custom questions for Nova to ask during the voice interview!")
    
    # Initialize session state for questions
    if 'custom_questions' not in st.session_state:
        st.session_state.custom_questions = []
    
    # ==================== QUESTION SOURCE SELECTION ====================
    
    question_source = st.radio(
        "📚 Choose how to set interview questions:",
        ["📤 Upload Document (PDF/TXT/Excel)", "✍️ Add Questions Manually", "🔄 Use Previous Questions"],
        horizontal=False
    )
    
    st.markdown("---")
    
    # ==================== OPTION 1: UPLOAD DOCUMENT ====================
    
    if question_source == "📤 Upload Document (PDF/TXT/Excel)":
        st.subheader("📤 Upload Questions Document")
        
        uploaded_file = st.file_uploader(
            "Upload questions file",
            type=['pdf', 'txt', 'xlsx', 'xls'],
            help="Upload PDF, TXT, or Excel file with interview questions (one per line/cell)"
        )
        
        if uploaded_file:
            with st.spinner("Processing file..."):
                questions = load_questions_from_file(uploaded_file)
                
                if questions:
                    st.session_state.custom_questions = questions
                    st.success(f"✅ Loaded {len(questions)} questions from {uploaded_file.name}")
                else:
                    st.error("❌ Could not extract questions from file")
    
    # ==================== OPTION 2: MANUAL ENTRY ====================
    
    elif question_source == "✍️ Add Questions Manually":
        st.subheader("✍️ Interview Questions")
        st.markdown("Add or edit questions Nova will ask during the voice interview:")
        
        # Display and edit questions
        questions_to_remove = []
        for i, question in enumerate(st.session_state.custom_questions):
            col1, col2 = st.columns([4, 1])
            with col1:
                new_question = st.text_input(
                    f"Question {i+1}",
                    value=question,
                    key=f"q_{i}",
                    label_visibility="collapsed"
                )
                st.session_state.custom_questions[i] = new_question
            with col2:
                if st.button("🗑️", key=f"del_{i}", help="Delete this question"):
                    questions_to_remove.append(i)
        
        # Remove questions
        for idx in sorted(questions_to_remove, reverse=True):
            st.session_state.custom_questions.pop(idx)
        
        # Add new question
        col1, col2 = st.columns([3, 1])
        with col1:
            new_question_input = st.text_input(
                "Add new question",
                key="new_question_input",
                placeholder="Enter a question..."
            )
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("➕ Add Question", use_container_width=True):
                if new_question_input.strip():
                    st.session_state.custom_questions.append(new_question_input.strip())
                    st.rerun()
    
    # ==================== OPTION 3: PREVIOUS QUESTIONS ====================
    
    elif question_source == "🔄 Use Previous Questions":
        st.subheader("🔄 Select from Previous Employees' Questions")
        
        employees, error = get_employees()
        
        if error or not employees:
            st.warning("No previous employees found")
        else:
            # Get unique question sets
            employee_questions = {}
            for emp in employees:
                if emp.get('interview') and emp['interview'].get('questions_json'):
                    try:
                        qs = json.loads(emp['interview']['questions_json'])
                        key = json.dumps(qs)
                        if key not in employee_questions:
                            employee_questions[key] = (qs, emp['name'])
                    except:
                        pass
            
            if not employee_questions:
                st.warning("No previous question sets found")
            else:
                options = [f"From {name} ({len(qs)} questions)" for qs, name in employee_questions.values()]
                selected = st.selectbox("Choose a question set:", options)
                
                if selected:
                    questions_list = list(employee_questions.values())
                    selected_idx = options.index(selected)
                    st.session_state.custom_questions = questions_list[selected_idx][0]
                    st.success("✅ Questions loaded!")
    
    st.markdown("---")
    
    # ==================== QUESTION PREVIEW ====================
    
    if st.session_state.custom_questions:
        with st.expander("📋 Preview Questions Nova Will Ask", expanded=True):
            for i, q in enumerate(st.session_state.custom_questions, 1):
                st.markdown(f'<div class="question-card">**Q{i}:** {q}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== EMPLOYEE FORM ====================
    
    st.subheader("👤 Employee Details")
    
    with st.form("add_employee_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Employee Name *", placeholder="e.g., Ravi Kumar")
            email = st.text_input("Email Address *", placeholder="e.g., ravi@company.com")
        
        with col2:
            department = st.selectbox(
                "Department *",
                ["Engineering", "HR", "Sales", "Marketing", "Finance", "Operations", "IT", "Customer Support"]
            )
            last_working_date = st.date_input(
                "Last Working Date *",
                min_value=date.today()
            )
        
        st.markdown("---")
        
        submitted = st.form_submit_button(
            "➕ Add Employee & Send Voice Interview Email",
            use_container_width=True
        )
        
        if submitted:
            if not name or not email:
                st.error("❌ Please fill all required fields!")
            elif "@" not in email:
                st.error("❌ Please enter a valid email!")
            elif not st.session_state.custom_questions:
                st.error("❌ Please add at least one question!")
            else:
                with st.spinner("Adding employee and sending voice interview email..."):
                    result, error = add_employee(
                        name, email, department,
                        last_working_date,
                        st.session_state.custom_questions
                    )
                    
                    if error:
                        st.error(f"❌ Error: {error}")
                    else:
                        st.success(f"✅ Employee added successfully!")
                        st.success(f"📧 Voice interview email sent to {email}")
                        st.balloons()
                        
                        st.info(f"""
                        **Employee Details:**
                        - Name: {name}
                        - Email: {email}
                        - Department: {department}
                        - Last Working Date: {last_working_date}
                        - Interview Type: 🎙️ Voice with Nova Sonic
                        - Questions: {len(st.session_state.custom_questions)} custom questions
                        """)
                        
                        # Clear the questions after successful submission
                        st.session_state.custom_questions = []

# ==================== PAGE 3: VIEW EMPLOYEES ====================

elif page == "👥 View Employees":
    st.markdown('<p class="main-header">👥 All Employees</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Resigned", "Completed"])
    
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    employees, error = get_employees()
    
    if error:
        st.error(f"Error: {error}")
    elif not employees:
        st.info("No employees found.")
    else:
        if status_filter != "All":
            employees = [emp for emp in employees if emp['status'] == status_filter]
        
        for emp in employees:
            interview = emp.get('interview', {})
            is_completed = interview and interview.get('completed', False)
            
            with st.expander(
                f"🎙️ {'✅' if is_completed else '⏳'} {emp['name']} - {emp['department']}",
                expanded=False
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Email:** {emp['email']}")
                    st.write(f"**Department:** {emp['department']}")
                    st.write(f"**Last Working Date:** {emp['last_working_date']}")
                
                with col2:
                    st.write(f"**Status:** {emp['status']}")
                    st.write(f"**Added On:** {emp['created_at'][:10]}")
                    if interview:
                        st.write(f"**Interview:** {'✅ Completed' if is_completed else '⏳ Pending'}")
                
                if is_completed and interview:
                    if st.button(f"👁️ View Voice Responses", key=f"view_{emp['id']}"):
                        st.session_state['view_interview_id'] = interview['id']
                        st.session_state['view_employee_name'] = emp['name']

# ==================== PAGE 4: VIEW RESPONSES ====================

# elif page == "📝 View Responses":
#     st.markdown('<p class="main-header">📝 Voice Interview Responses</p>', unsafe_allow_html=True)
#     st.markdown("---")
    
#     employees, error = get_employees()
    
#     if error:
#         st.error(f"Error: {error}")
#     elif not employees:
#         st.info("No employees found.")
#     else:
#         completed = [emp for emp in employees if emp.get('interview', {}).get('completed')]
        
#         if not completed:
#             st.info("No completed interviews yet.")
#         else:
#             employee_options = {f"{emp['name']} ({emp['email']})": emp for emp in completed}
#             selected_name = st.selectbox("Select Employee", list(employee_options.keys()))
            
#             if selected_name:
#                 selected_emp = employee_options[selected_name]
#                 interview = selected_emp['interview']
                
#                 st.markdown("---")
#                 st.subheader(f"🎙️ Voice Interview Responses - {selected_emp['name']}")
                
#                 col1, col2, col3 = st.columns(3)
#                 with col1:
#                     st.write(f"**Department:** {selected_emp['department']}")
#                 with col2:
#                     st.write(f"**Email:** {selected_emp['email']}")
#                 with col3:
#                     st.write(f"**Completed On:** {interview['created_at'][:10]}")
                
#                 st.markdown("---")
                
#                 responses, error = get_interview_responses(interview['id'])
                
#                 if error:
#                     st.error(f"Error: {error}")
#                 elif not responses:
#                     st.warning("No responses found.")
#                 else:
#                     for i, response in enumerate(responses, 1):
#                         st.markdown(f"**Q{i}: {response['question']}**")
#                         st.info(f"📝 {response['answer']}")
                        
#                         if response.get('audio_url'):
#                             st.audio(response['audio_url'])
                        
#                         st.markdown("")


# Replace the entire "📝 View Responses" section in your Streamlit app

elif page == "📝 View Responses":
    st.markdown('<p class="main-header">📝 Voice Interview Responses</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    employees, error = get_employees()
    
    if error:
        st.error(f"Error: {error}")
    elif not employees:
        st.info("No employees found.")
    else:
        # DEBUG: Show all employees data
        with st.expander("🔍 Debug: View All Employees Data", expanded=False):
            st.json(employees)
        
        # Filter for completed interviews
        completed = []
        for emp in employees:
            st.write(f"Checking employee: {emp.get('name')}")
            st.write(f"Has interview key: {'interview' in emp}")
            
            if 'interview' in emp and emp['interview'] is not None:
                interview = emp['interview']
             #   st.write(f"Interview data: {interview}")
                st.write(f"Completed status: {interview.get('completed')}")
                
                if interview.get('completed') == True or interview.get('completed') == 'true':
                    completed.append(emp)
                    st.success(f"✅ Added {emp['name']} to completed list")
            else:
                st.warning(f"⚠️ {emp['name']} has no interview data")
        
        st.info(f"Total employees: {len(employees)}, Completed interviews: {len(completed)}")
        
        if not completed:
            st.warning("No completed interviews found.")
            st.info("💡 Tip: Make sure the interview is marked as completed in the database.")
        else:
            employee_options = {f"{emp['name']} ({emp['email']})": emp for emp in completed}
            selected_name = st.selectbox("Select Employee", list(employee_options.keys()))
            
            if selected_name:
                selected_emp = employee_options[selected_name]
                interview = selected_emp['interview']
                
                st.markdown("---")
                st.subheader(f"🎙️ Voice Interview Responses - {selected_emp['name']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Department:** {selected_emp['department']}")
                with col2:
                    st.write(f"**Email:** {selected_emp['email']}")
                with col3:
                    completed_date = interview.get('created_at', 'N/A')
                    if completed_date and completed_date != 'N/A':
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(completed_date.replace('Z', '+00:00'))
                            completed_date = dt.strftime('%Y-%m-%d')
                        except:
                            completed_date = completed_date[:10] if len(completed_date) > 10 else completed_date
                    st.write(f"**Completed On:** {completed_date}")
                
                st.markdown("---")
                
                # Fetch responses
                responses, error = get_interview_responses(interview['id'])
                
                if error:
                    st.error(f"Error loading responses: {error}")
                elif not responses:
                    st.warning("No responses found for this interview.")
                else:
                    for i, response in enumerate(responses, 1):
                        with st.container():
                            st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
                            st.markdown(f"**🤖 Nova:** {response['question']}")
                            st.markdown(f"**👤 {selected_emp['name']}:** {response['answer']}")
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown("")

# ==================== FOOTER ====================

st.sidebar.markdown("---")
st.sidebar.markdown("**System Status:**")
st.sidebar.success("✅ Backend Connected")
st.sidebar.caption("Version 4.0.0 - Dynamic Questions Support")