# import streamlit as st
# import requests
# import pandas as pd
# from datetime import datetime, date
# import os
# from dotenv import load_dotenv

# load_dotenv()

# # API Configuration
# API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# # Page Configuration
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
#     .metric-card {
#         background-color: #f0f2f6;
#         padding: 20px;
#         border-radius: 10px;
#         text-align: center;
#     }
# </style>
# """, unsafe_allow_html=True)

# # ==================== API FUNCTIONS ====================

# def add_employee(name, email, department, last_working_date):
#     """Add new employee via API"""
#     try:
#         data = {
#             "name": name,
#             "email": email,
#             "department": department,
#             "last_working_date": str(last_working_date)
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

# def resend_email(employee_id):
#     """Resend interview email"""
#     try:
#         response = requests.post(f"{API_BASE_URL}/employees/{employee_id}/resend-email")
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

# # ==================== SIDEBAR NAVIGATION ====================

# st.sidebar.title("🏢 HR Dashboard")
# st.sidebar.markdown("---")

# page = st.sidebar.selectbox(
#     "Navigation",
#     ["📊 Dashboard", "➕ Add Employee", "👥 View Employees", "📝 View Responses"]
# )

# st.sidebar.markdown("---")
# st.sidebar.info("Exit Interview Management System")

# # ==================== PAGE 1: DASHBOARD ====================

# if page == "📊 Dashboard":
#     st.markdown('<p class="main-header">📊 Exit Interview Dashboard</p>', unsafe_allow_html=True)
#     st.markdown("---")
    
#     # Get statistics
#     stats, error = get_statistics()
    
#     if error:
#         st.error(f"⚠️ Error connecting to backend: {error}")
#         st.info("Make sure backend is running: `python app/main.py`")
#     else:
#         # Display metrics
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             st.metric(
#                 label="Total Resignations",
#                 value=stats['total_resignations'],
#                 delta=None
#             )
        
#         with col2:
#             st.metric(
#                 label="Completed Interviews",
#                 value=stats['completed_interviews'],
#                 delta=None
#             )
        
#         with col3:
#             st.metric(
#                 label="Pending Interviews",
#                 value=stats['pending_interviews'],
#                 delta=None
#             )
        
#         with col4:
#             st.metric(
#                 label="Completion Rate",
#                 value=f"{stats['completion_rate']:.1f}%",
#                 delta=None
#             )
        
#         st.markdown("---")
        
#         # Recent employees
#         st.subheader("📋 Recent Exit Interviews")
        
#         employees, error = get_employees()
        
#         if error:
#             st.error(f"Error loading employees: {error}")
#         elif not employees:
#             st.info("No employees added yet. Use 'Add Employee' to get started.")
#         else:
#             # Create dataframe
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
    
#     st.info("💡 After adding, an exit interview email will be sent automatically!")
    
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
#         submitted = st.form_submit_button("➕ Add Employee & Send Email", use_container_width=True)
        
#         if submitted:
#             # Validation
#             if not name or not email:
#                 st.error("❌ Please fill all required fields!")
#             elif "@" not in email:
#                 st.error("❌ Please enter a valid email address!")
#             else:
#                 with st.spinner("Adding employee and sending email..."):
#                     result, error = add_employee(name, email, department, last_working_date)
                    
#                     if error:
#                         st.error(f"❌ Error: {error}")
#                         if "already exists" in str(error):
#                             st.warning("This email is already registered in the system.")
#                     else:
#                         st.success(f"✅ Employee added successfully!")
#                         st.success(f"📧 Exit interview email sent to {email}")
#                         st.balloons()
                        
#                         # Show details
#                         st.info(f"""
#                         **Employee Details:**
#                         - Name: {name}
#                         - Email: {email}
#                         - Department: {department}
#                         - Last Working Date: {last_working_date}
#                         """)

# # ==================== PAGE 3: VIEW EMPLOYEES ====================

# elif page == "👥 View Employees":
#     st.markdown('<p class="main-header">👥 All Employees</p>', unsafe_allow_html=True)
#     st.markdown("---")
    
#     # Filters
#     col1, col2, col3 = st.columns([2, 2, 1])
    
#     with col1:
#         status_filter = st.selectbox("Filter by Status", ["All", "Resigned", "Completed"])
    
#     with col3:
#         if st.button("🔄 Refresh", use_container_width=True):
#             st.rerun()
    
#     st.markdown("---")
    
#     # Get employees
#     employees, error = get_employees()
    
#     if error:
#         st.error(f"Error: {error}")
#     elif not employees:
#         st.info("No employees found.")
#     else:
#         # Apply filter
#         if status_filter != "All":
#             employees = [emp for emp in employees if emp['status'] == status_filter]
        
#         # Display as cards
#         for emp in employees:
#             interview = emp.get('interview', {})
#             is_completed = interview and interview.get('completed', False)
            
#             with st.expander(f"{'✅' if is_completed else '⏳'} {emp['name']} - {emp['department']}", expanded=False):
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     st.write(f"**Email:** {emp['email']}")
#                     st.write(f"**Department:** {emp['department']}")
#                     st.write(f"**Last Working Date:** {emp['last_working_date']}")
                
#                 with col2:
#                     st.write(f"**Status:** {emp['status']}")
#                     st.write(f"**Added On:** {emp['created_at'][:10]}")
#                     if interview:
#                         st.write(f"**Interview Status:** {'✅ Completed' if is_completed else '⏳ Pending'}")
                
#                 # Action buttons
#                 col_btn1, col_btn2, col_btn3 = st.columns(3)
                
#                 with col_btn1:
#                     if not is_completed:
#                         if st.button(f"📧 Resend Email", key=f"resend_{emp['id']}"):
#                             with st.spinner("Sending email..."):
#                                 result, error = resend_email(emp['id'])
#                                 if error:
#                                     st.error(f"Error: {error}")
#                                 else:
#                                     st.success("✅ Email sent!")
                
#                 with col_btn2:
#                     if is_completed and interview:
#                         if st.button(f"👁️ View Responses", key=f"view_{emp['id']}"):
#                             st.session_state['view_interview_id'] = interview['id']
#                             st.session_state['view_employee_name'] = emp['name']

# # ==================== PAGE 4: VIEW RESPONSES ====================

# elif page == "📝 View Responses":
#     st.markdown('<p class="main-header">📝 Interview Responses</p>', unsafe_allow_html=True)
#     st.markdown("---")
    
#     # Get all employees
#     employees, error = get_employees()
    
#     if error:
#         st.error(f"Error: {error}")
#     elif not employees:
#         st.info("No employees found.")
#     else:
#         # Filter only completed interviews
#         completed = [emp for emp in employees if emp.get('interview', {}).get('completed')]
        
#         if not completed:
#             st.info("No completed interviews yet.")
#         else:
#             # Select employee
#             employee_options = {f"{emp['name']} ({emp['email']})": emp for emp in completed}
#             selected_name = st.selectbox("Select Employee", list(employee_options.keys()))
            
#             if selected_name:
#                 selected_emp = employee_options[selected_name]
#                 interview = selected_emp['interview']
                
#                 st.markdown("---")
#                 st.subheader(f"📋 Interview Responses - {selected_emp['name']}")
                
#                 col1, col2, col3 = st.columns(3)
#                 with col1:
#                     st.write(f"**Department:** {selected_emp['department']}")
#                 with col2:
#                     st.write(f"**Email:** {selected_emp['email']}")
#                 with col3:
#                     st.write(f"**Completed On:** {interview['created_at'][:10]}")
                
#                 st.markdown("---")
                
#                 # Get responses
#                 responses, error = get_interview_responses(interview['id'])
                
#                 if error:
#                     st.error(f"Error loading responses: {error}")
#                 elif not responses:
#                     st.warning("No responses found.")
#                 else:
#                     # Display responses
#                     for i, response in enumerate(responses, 1):
#                         st.markdown(f"**Q{i}: {response['question']}**")
#                         st.info(f"📝 {response['answer']}")
#                         st.markdown("")

# # ==================== FOOTER ====================

# st.sidebar.markdown("---")
# st.sidebar.markdown("**System Status:**")
# st.sidebar.success("✅ Backend Connected")
# st.sidebar.caption("Version 1.0.0")





# File: pages/Exit_Interview_Chat.py

import streamlit as st
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="AI Exit Interview - Nova",
    page_icon="🤖",
    layout="wide"
)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 30px;
        font-size: 1.1rem;
    }
    .chat-message {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        animation: fadeIn 0.5s;
    }
    .bot-message {
        background-color: #f0f2f6;
        border-left: 4px solid #1f77b4;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #4CAF50;
        margin-left: 20px;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .status-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .status-active {
        background-color: #4CAF50;
        color: white;
    }
    .status-completed {
        background-color: #2196F3;
        color: white;
    }
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Get token from URL
query_params = st.query_params
token = query_params.get("token", None)

if not token:
    st.error("❌ Invalid or missing interview link!")
    st.info("Please use the link provided in your email.")
    st.stop()

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'interview_complete' not in st.session_state:
    st.session_state.interview_complete = False
if 'interview_data' not in st.session_state:
    st.session_state.interview_data = None
if 'conversation_started' not in st.session_state:
    st.session_state.conversation_started = False

# Fetch interview details
if st.session_state.interview_data is None:
    try:
        response = requests.get(f"{API_BASE_URL}/interviews/token/{token}")
        response.raise_for_status()
        st.session_state.interview_data = response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error: {str(e)}")
        if "already completed" in str(e).lower():
            st.success("✅ This interview has already been completed. Thank you!")
        st.stop()

interview_data = st.session_state.interview_data
employee_name = interview_data.get('employee_name', 'Employee')
department = interview_data.get('employee_department', 'Unknown')

def call_ai_chat(user_message):
    """Call backend AI chat endpoint"""
    try:
        # Build history for API
        history = []
        for msg in st.session_state.messages:
            history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        response = requests.post(
            f"{API_BASE_URL}/interviews/token/{token}/chat",
            json={
                "message": user_message,
                "history": history
            }
        )
        response.raise_for_status()
        result = response.json()
        return result['response']
    except Exception as e:
        return f"I apologize, but I'm having trouble connecting. Error: {str(e)}"

def save_interview_responses():
    """Save all interview responses to database"""
    responses = []
    current_question = None
    
    # Extract Q&A pairs from conversation
    for msg in st.session_state.messages:
        if msg['role'] == 'assistant' and '?' in msg['content']:
            current_question = msg['content']
        elif msg['role'] == 'user' and current_question:
            responses.append({
                "question": current_question,
                "answer": msg['content']
            })
            current_question = None
    
    # Add full conversation transcript
    full_transcript = "\n\n".join([
        f"{'🤖 Nova' if msg['role'] == 'assistant' else '👤 Employee'}: {msg['content']}"
        for msg in st.session_state.messages
    ])
    
    responses.append({
        "question": "Full Interview Transcript",
        "answer": full_transcript
    })
    
    # Submit to backend
    try:
        submit_data = {"responses": responses}
        response = requests.post(
            f"{API_BASE_URL}/interviews/token/{token}/submit",
            json=submit_data
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error saving interview: {str(e)}")
        return False

# Header
st.markdown('<p class="main-title">🤖 AI Exit Interview with Nova</p>', unsafe_allow_html=True)
st.markdown(f'<p class="subtitle">Welcome, <strong>{employee_name}</strong> from <strong>{department}</strong>! Nova will guide you through your exit interview.</p>', unsafe_allow_html=True)

# Info box
st.markdown(f"""
<div class="info-box">
    <h3 style="margin-top: 0;">💡 How this works:</h3>
    <p style="margin-bottom: 0;">
    • <strong>Nova</strong> is an AI assistant that will ask you questions about your experience<br>
    • Have a <strong>natural conversation</strong> - just like talking to HR<br>
    • Take your time - there's no rush<br>
    • Your responses are <strong>confidential</strong> and help us improve
    </p>
</div>
""", unsafe_allow_html=True)

# Status badge
if st.session_state.interview_complete:
    st.markdown('<span class="status-badge status-completed">✅ COMPLETED</span>', unsafe_allow_html=True)
else:
    st.markdown('<span class="status-badge status-active">🟢 IN PROGRESS</span>', unsafe_allow_html=True)

st.markdown("---")

# Start conversation automatically
if not st.session_state.conversation_started and not st.session_state.interview_complete:
    with st.spinner("Nova is preparing your interview..."):
        initial_message = call_ai_chat(f"Hello, I'm {employee_name}. I'm here for my exit interview.")
        st.session_state.messages.append({
            "role": "user",
            "content": f"Hello, I'm {employee_name}. I'm here for my exit interview.",
            "timestamp": datetime.now().strftime("%H:%M")
        })
        st.session_state.messages.append({
            "role": "assistant",
            "content": initial_message,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        st.session_state.conversation_started = True
        st.rerun()

# Chat container
chat_container = st.container()

# Display chat history
with chat_container:
    for message in st.session_state.messages:
        if message['role'] == 'assistant':
            st.markdown(f"""
            <div class="chat-message bot-message">
                <strong>🤖 Nova</strong> <small style="color: #999;">{message['timestamp']}</small><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You</strong> <small style="color: #999;">{message['timestamp']}</small><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)

# Check if interview is complete
if st.session_state.messages and "INTERVIEW_COMPLETE" in st.session_state.messages[-1].get('content', ''):
    if not st.session_state.interview_complete:
        st.session_state.interview_complete = True
        if save_interview_responses():
            st.success("✅ Interview completed successfully! Thank you for your valuable feedback.")
            st.balloons()
            st.info("You can now close this window. Your responses have been securely saved.")
        st.stop()

# User input
if not st.session_state.interview_complete:
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "Your response:",
                key="user_input",
                placeholder="Type your answer here...",
                label_visibility="collapsed"
            )
        with col2:
            send_button = st.form_submit_button("Send 📤", use_container_width=True)
        
        if send_button and user_input.strip():
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            
            # Get AI response
            with st.spinner("Nova is thinking..."):
                ai_response = call_ai_chat(user_input)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
            
            st.rerun()
else:
    st.info("✅ Interview completed. Thank you!")

# Sidebar info
with st.sidebar:
    st.markdown("### 📋 Interview Progress")
    progress = min(len(st.session_state.messages) / 20, 1.0)
    st.progress(progress)
    st.caption(f"{len(st.session_state.messages)} messages exchanged")
    
    if progress > 0.5:
        st.success("Great progress! Keep going.")
    
    st.markdown("---")
    st.markdown("### 🤖 About Nova")
    st.info("""
    **Nova** is an AI assistant designed to:
    - Conduct natural conversations
    - Ask relevant follow-up questions
    - Ensure comprehensive feedback
    - Make the process comfortable
    """)
    
    st.markdown("---")
    st.markdown("### 🔒 Privacy")
    st.caption("""
    Your responses are confidential and used only to improve our workplace. 
    Powered by Claude Sonnet 4 (Nova Sonic).
    """)