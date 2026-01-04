"""
Student Test Access Page

This page handles:
- Test ID from URL parameters
- Student name and access code input
- Test validation (exists, active, not expired)
- Navigation to exam interface
"""

import streamlit as st
from datetime import datetime, timezone
from utils.firebase import get_test_by_id, validate_access_code
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(
    page_title="Take Test - comPASS",
    page_icon="📝",
    layout="centered"
)

# Custom CSS for mobile-first design
st.markdown("""
<style>
    .main {
        padding: 2rem 1rem;
    }
    
    .access-card {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 2rem 0;
    }
    
    .test-info {
        background: #e7f3ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #0066cc;
        margin: 1rem 0;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        padding: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ========================================
# GET TEST ID (SESSION FIRST, URL SECOND)
# ========================================

query_params = st.query_params

test_id = None

# 1️⃣ Prefer session_state (navigation inside app)
if "active_test_id" in st.session_state:
    test_id = st.session_state["active_test_id"]

# 2️⃣ Fallback to URL param (direct link / refresh)
elif "id" in query_params:
    test_id = query_params.get("id")
    if isinstance(test_id, list):
        test_id = test_id[0]

if not test_id or not str(test_id).strip():
    st.error("❌ Invalid test link")
    st.markdown("""
    ### No Test ID Provided
    
    Please make sure you're using the complete test link shared by your teacher.
    
    **Expected format:**
    `https://your-app.hf.space/take_test?id=TEST_ID_HERE`
    """)
    st.stop()

# ✅ Freeze it for rest of page
test_id = test_id.strip()
st.session_state["active_test_id"] = test_id

# ========================================
# FETCH TEST DETAILS
# ========================================

with st.spinner("Loading test..."):
    test = get_test_by_id(test_id)

if not test:
    st.error("❌ Test not found")
    st.markdown("""
    ### Test Not Found
    
    The test you're trying to access doesn't exist or has been deleted.
    
    Please contact your teacher for the correct test link.
    """)
    st.stop()

# Check if test is expired
expiry_time = test.get('expiry_time')
is_expired = False

if isinstance(expiry_time, datetime):
    # Ensure timezone-aware comparison
    if expiry_time.tzinfo is None:
        expiry_time = expiry_time.replace(tzinfo=timezone.utc)
    
    now_utc = datetime.now(timezone.utc)
    is_expired = now_utc > expiry_time
elif test.get('status') == 'expired':
    is_expired = True

# ========================================
# HEADER
# ========================================

st.title("📝 Take Test")
st.markdown(f"## {test['title']}")

# Display test information
st.markdown(
    f"""
    <div class="test-info">
        <p><strong>Subject:</strong> {test['subject']}</p>
        <p><strong>Number of Questions:</strong> {test['total_questions']}</p>
        <p><strong>Duration:</strong> {test['duration']} minutes</p>
        <p><strong>Status:</strong> {'🔴 EXPIRED' if is_expired else '🟢 ACTIVE'}</p>
    </div>
    """,
    unsafe_allow_html=True
)


# ========================================
# HANDLE EXPIRED TEST
# ========================================

if is_expired:
    st.error("❌ This test has expired")
    st.markdown("""
    ### Test No Longer Available
    
    This test closed on **{}**.
    
    Please contact your teacher if you believe this is an error.
    """.format(expiry_time.strftime("%B %d, %Y at %I:%M %p") if isinstance(expiry_time, datetime) else "the expiry date"))
    st.stop()

# ========================================
# ACCESS FORM
# ========================================

st.markdown("")
st.markdown("")
st.markdown("### Enter Your Details")

# Access form
with st.form("access_form", clear_on_submit=False):
    student_name = st.text_input(
        "Your Full Name *",
        placeholder="e.g., Muhammed Fatimoh",
        help="Enter your full name as it should appear in results",
        max_chars=100
    )
    
    access_code = st.text_input(
        "Access Code *",
        placeholder="Enter the 6-character code",
        help="Your teacher provided this code",
        max_chars=8
    ).upper()
    
    st.markdown("")
    st.markdown("")
    
    # Important instructions
    with st.expander("⚠️ Important Instructions - Read Before Starting"):
        st.markdown("""
        **Before you begin:**
        1. ✅ Ensure you have a stable internet connection
        2. ✅ Find a quiet place with minimal distractions
        3. ✅ Have scratch paper ready if needed
        4. ✅ Make sure your device is charged or plugged in
        
        **During the test:**
        - Answer questions one at a time
        - You can navigate back to previous questions
        - Your answers are saved automatically
        - A timer will be visible at all times
        - The test will auto-submit when time expires
        
        **Rules:**
        - Do not refresh the page during the test
        - Do not close your browser until submission is complete
        - You cannot retake the test once submitted
        - No external help or resources allowed
        
        **Technical Issues:**
        - Take a screenshot of any error messages
        """)
    
    # Acknowledgment checkbox
    acknowledge = st.checkbox(
        "I have read and understood the instructions above",
        key="acknowledge_instructions"
    )
    
    submit_access = st.form_submit_button(
        "Verify and Start Test",
        type="primary",
        use_container_width=True
    )

# ========================================
# HANDLE ACCESS SUBMISSION
# ========================================

if submit_access:
    # Validation
    if not student_name or not access_code:
        st.error("❌ Please enter both your name and access code")
    elif len(student_name.strip()) < 3:
        st.error("❌ Please enter your full name (at least 3 characters)")
    elif not acknowledge:
        st.error("❌ Please read and acknowledge the instructions")
    else:
        with st.spinner("Verifying access code..."):
            # Validate access code
            is_valid = validate_access_code(test_id, access_code)
            
            if is_valid:
                # Create test session
                st.session_state.test_session = {
                    'test_id': test_id,
                    'student_name': student_name.strip(),
                    'test_title': test['title'],
                    'test_subject': test['subject'],
                    'total_questions': test['total_questions'],
                    'duration': test['duration'],
                    'start_time': datetime.now(timezone.utc),
                    'current_question': 0,
                    'answers': {},  # question_id: selected_option
                    'visited_questions': set()
                }
                
                st.success("✅ Access granted!")
                st.balloons()
                st.info("Redirecting to test...")
                
                # Redirect to exam interface
                st.switch_page("pages/exam_interface.py")
            else:
                st.error("❌ Invalid access code")
                st.markdown("""
                **Access Denied**
                
                The access code you entered is incorrect or the test is no longer active.
                
                Please check:
                - The access code is correct (case-insensitive)
                - You're using the most recent test link from your teacher
                - The test hasn't expired
                """)

# ========================================
# FOOTER
# ========================================

st.markdown("")
st.markdown("")

with st.expander("❓ Frequently Asked Questions"):
    st.markdown("""
    **Q: What if I don't have the access code?**  
    A: Contact your teacher. They will provide you with the access code.
    
    **Q: Can I take the test multiple times?**  
    A: No, each student can only submit once per test.
    
    **Q: What happens if my internet disconnects?**  
    A: Your answers are saved automatically. If you reconnect before time expires, you can continue.
    
    **Q: Can I review my answers before submitting?**  
    A: Yes, you can navigate between questions and change answers before final submission.
    
    **Q: What if I run out of time?**  
    A: The test will automatically submit when time expires. Make sure to answer all questions!
    """)

st.caption("comPASS v1.0 | Student Test Access")