"""
Create Test Page

This page handles:
- Test metadata input (title, subject, duration, expiry, access code)
- CSV question upload
- Question validation
- Test creation in Firestore
- Test link generation
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import string
from utils.auth import require_authentication, get_current_user_id
from utils.firebase import create_test, create_questions_batch

# Protect this page - require login
require_authentication()

# Page configuration
st.set_page_config(
    page_title="Create Test - comPASS",
    page_icon="➕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def is_mobile_device():
    """Detect if user is on mobile device via JavaScript."""
    import streamlit.components.v1 as components
    
    # Use JavaScript to detect mobile
    mobile_check = components.html(
        """
        <script>
        function isMobile() {
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) 
                   || window.innerWidth <= 768;
        }
        
        // Send result to Streamlit
        const mobile = isMobile();
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: mobile
        }, '*');
        </script>
        """,
        height=0
    )
    
    return mobile_check if mobile_check is not None else False

# Custom CSS
st.markdown("""
<style>
    .success-box {
        padding: 1.5rem;
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .info-box {
        padding: 1rem;
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ========================================
# STATE MANAGEMENT
# ========================================

def init_form_state():
    """Initialize form state with defaults - called ONCE per fresh form"""
    default_expiry = datetime.now() + timedelta(days=7)
    st.session_state.form_expiry_date = default_expiry.date()
    st.session_state.form_expiry_time = default_expiry.time()
    st.session_state.form_access_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def clear_form_state():
    """Clear all form-related state"""
    keys_to_clear = [
        'form_expiry_date', 'form_expiry_time', 'form_access_code',
        'test_created', 'created_test_id', 'created_access_code',
        'created_questions_count', 'created_expiry', 'success_ui_shown'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# Check if returning from another page with stale success state
if 'last_page' not in st.session_state:
    st.session_state.last_page = 'create_test'

if st.session_state.last_page != 'create_test':
    # User is returning from elsewhere - clear success state
    if st.session_state.get('test_created'):
        clear_form_state()

st.session_state.last_page = 'create_test'

# Initialize form defaults if not present
if 'form_expiry_date' not in st.session_state:
    init_form_state()

# ========================================
# HEADER
# ========================================

st.title("➕ Create New Test")
st.markdown("Upload questions and configure your test parameters")

st.markdown("")
st.markdown("")

# ========================================
# CSV FORMAT GUIDE
# ========================================

with st.expander("📋 CSV Format Guide - Click to View Required Format"):
    st.markdown("""    
    ### Important Notes
    - Column names are case-sensitive
    - Use double quotes for text with commas
    - `correct_option` must be exactly A, B, C, or D (case-insensitive)
    - No empty cells allowed
    """)
    
    # Download sample CSV
    sample_data = {
        'question': [
            "What is the SI unit of force?",
            "Which law states that for every action there is an equal and opposite reaction?",
            "What is the speed of light in vacuum?"
        ],
        'option_a': ["Newton", "Newton's First Law", "3 × 10^8 m/s"],
        'option_b': ["Joule", "Newton's Second Law", "3 × 10^6 m/s"],
        'option_c': ["Watt", "Newton's Third Law", "3 × 10^10 m/s"],
        'option_d': ["Pascal", "Law of Gravitation", "3 × 10^5 m/s"],
        'correct_option': ["A", "C", "A"],
        'topic': ["Units", "Mechanics", "Waves and Optics"],
    }
    sample_df = pd.DataFrame(sample_data)

    st.dataframe(sample_df, use_container_width=True, height=200)
    
    csv = sample_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Sample CSV Template",
        data=csv,
        file_name="compass_sample_questions.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.markdown("")
    st.info("💡 After downloading, transfer this file to your desktop and create the test there.")

st.markdown("")
st.markdown("")

# ========================================
# STEP 1: TEST METADATA
# ========================================

st.markdown("### Step 1: Test Information")

col1, col2 = st.columns(2)

with col1:
    test_title = st.text_input(
        "Test Title *",
        placeholder="e.g., JAMB Physics Mock Test 1",
        help="Give your test a descriptive name"
    )
    
    subject = st.text_input(
        "Subject *",
        placeholder="e.g., Physics",
        help="Subject area being tested"
    )

with col2:
    duration = st.number_input(
        "Duration (minutes) *",
        min_value=5,
        max_value=240,
        value=45,
        step=5,
        help="How long students have to complete the test"
    )
    
    expiry_date = st.date_input(
        "Expiry Date *",
        value=st.session_state.form_expiry_date,
        min_value=datetime.now().date(),
        help="Last date students can take this test"
    )
    
    # Update session state when user changes date
    if expiry_date != st.session_state.form_expiry_date:
        st.session_state.form_expiry_date = expiry_date
 
    expiry_time = st.time_input(
        "Expiry Time *",
        value=st.session_state.form_expiry_time,
        help="Time when test closes on expiry date"
    )
    
    # Update session state when user changes time
    if expiry_time != st.session_state.form_expiry_time:
        st.session_state.form_expiry_time = expiry_time

col1, col2 = st.columns([3, 1])

with col1:
    access_code = st.text_input(
        "Access Code *",
        value=st.session_state.form_access_code,
        max_chars=8,
        help="Students need this code to access the test"
    )
    
    # Update session state if user manually edits
    if access_code != st.session_state.form_access_code:
        st.session_state.form_access_code = access_code

with col2:
    if st.button("🔄 Generate New", use_container_width=True):
        st.session_state.form_access_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        st.rerun()

st.markdown("")
st.markdown("")

# ========================================
# STEP 2: UPLOAD QUESTIONS
# ========================================

st.markdown("### Step 2: Upload Questions (CSV)")

# Initialize session state
if 'csv_processed' not in st.session_state:
    st.session_state.csv_processed = False
if 'csv_df' not in st.session_state:
    st.session_state.csv_df = None
if 'csv_name' not in st.session_state:
    st.session_state.csv_name = None
if 'questions_valid' not in st.session_state:
    st.session_state.questions_valid = False
if 'questions_data' not in st.session_state:
    st.session_state.questions_data = []
if 'device_checked' not in st.session_state:
    st.session_state.device_checked = False
if 'is_mobile' not in st.session_state:
    st.session_state.is_mobile = False

# Detect device type once
if not st.session_state.device_checked:
    # Simple viewport-based detection (more reliable than JS injection)
    st.markdown("""
    <script>
    const mobile = window.innerWidth <= 768 || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    window.parent.postMessage({isMobile: mobile}, '*');
    </script>
    """, unsafe_allow_html=True)
    
    # Fallback: assume desktop if cannot detect
    # Mobile users will see the warning message either way
    st.session_state.device_checked = True

# Check viewport width via CSS media query approach
viewport_check = st.empty()
with viewport_check:
    # Use CSS to detect viewport and update session state
    mobile_detected = st.checkbox(
        "I'm using a mobile device (auto-detected)",
        key="mobile_checkbox",
        value=False,
        help="Automatic detection based on screen size"
    )
    st.session_state.is_mobile = mobile_detected

# Clear the detection checkbox
viewport_check.empty()

# Simplified detection: Check user agent via query params or manual flag
# More reliable: Let user self-identify if upload fails
if not st.session_state.csv_processed:
    # Show mobile warning first
    st.info("ℹ️ **Choose your Device Type**")

    device_type = st.radio(
        "What device are you using?",
        ["Desktop / Laptop", "Mobile / Tablet"],
        horizontal=True
    )
    st.markdown("")
    
    # Conditional upload based on device
    if device_type == "Mobile / Tablet":
        # Mobile: Show restriction message
        st.warning("📱 **Mobile Upload Restricted**")
        st.markdown("""
        ### Question CSV Upload Unavailable on Mobile
        
        Due to browser limitations, CSV file uploads are currently supported on **desktop browsers only**.
        
        **To create a test with questions:**
        1. Switch to a laptop or desktop computer
        2. Access comPASS in a desktop browser (Chrome, Firefox, Safari, Edge)
        3. Complete the test creation with CSV upload
        
        **On mobile, you can:**
        - ✅ View existing tests
        - ✅ Monitor submissions
        - ✅ Download reports
        - ✅ Manage test settings
        
        **Need help?**
        - Contact support if you only have mobile access
        - Download the sample CSV template for desktop use
        """)

        # Stop further processing
        questions_valid = False
        questions_data = []
    
    else:
        # Desktop: Normal file upload
        
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Upload your questions in CSV format (see format guide above)",
            key="csv_file_uploader"
        )
        
        if uploaded_file is not None:
            try:
                # Read file content immediately
                bytes_data = uploaded_file.read()
                file_name = uploaded_file.name
                
                # Validate size
                if len(bytes_data) > 5 * 1024 * 1024:
                    st.error("❌ File too large. Maximum size is 5MB.")
                    st.stop()
                
                # Parse CSV from bytes
                import io
                df = pd.read_csv(io.BytesIO(bytes_data))
                
                # Store in session state
                st.session_state.csv_df = df
                st.session_state.csv_name = file_name
                st.session_state.csv_processed = True
                
                # Immediate rerun
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error reading CSV: {str(e)}")
                st.info("💡 Ensure file is valid CSV format")

else:
    # File already processed - show validation
    df = st.session_state.csv_df
    
    st.info(f"📄 File loaded: **{st.session_state.csv_name}** ({len(df)} rows)")
    
    # Validation section
    st.markdown("#### Validation Results")
    
    validation_errors = []
    validation_warnings = []
    
    # Required columns
    required_columns = [
        'question', 'option_a', 'option_b', 'option_c', 'option_d',
        'correct_option', 'topic'
    ]
    
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        validation_errors.append(f"❌ Missing columns: {', '.join(missing)}")
    
    # Empty cells
    if df.isnull().any().any():
        empty_locs = []
        for col in df.columns:
            empty_rows = df[df[col].isnull()].index.tolist()
            if empty_rows:
                empty_locs.append(f"{col}: rows {empty_rows}")
        validation_errors.append(f"❌ Empty cells in: {', '.join(empty_locs)}")
    
    # Correct option validation
    if 'correct_option' in df.columns:
        df['correct_option'] = df['correct_option'].astype(str).str.upper().str.strip()
        invalid_opts = df[~df['correct_option'].isin(['A', 'B', 'C', 'D'])]
        if not invalid_opts.empty:
            validation_errors.append(
                f"❌ Invalid correct_option in rows: {invalid_opts.index.tolist()}. Must be A/B/C/D"
            )

    # Question length
    if 'question' in df.columns:
        long_qs = df[df['question'].astype(str).str.len() > 500]
        if not long_qs.empty:
            validation_warnings.append(
                f"⚠️ Long questions (>500 chars) in rows: {long_qs.index.tolist()}"
            )
    
    # Display results
    for error in validation_errors:
        st.error(error)
    for warning in validation_warnings:
        st.warning(warning)
    
    if not validation_errors:
        st.session_state.questions_valid = True
        st.session_state.questions_data = df.to_dict('records')
        st.success(f"✅ **Validation Passed!** {len(df)} questions ready")
        
        with st.expander("👀 Preview Questions"):
            st.dataframe(df, use_container_width=True)
            
            st.markdown("#### Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Questions", len(df))
            with col2:
                if 'topic' in df.columns:
                    st.metric("Unique Topics", df['topic'].nunique())
    else:
        st.error("❌ Fix validation errors above")
        st.session_state.questions_valid = False
        st.session_state.questions_data = []
    
    # Remove file button
    if st.button("🗑️ Remove & Upload New", key="remove_csv"):
        st.session_state.csv_processed = False
        st.session_state.csv_df = None
        st.session_state.csv_name = None
        st.session_state.questions_valid = False
        st.session_state.questions_data = []
        st.rerun()

# Get values for Step 3
questions_valid = st.session_state.questions_valid
questions_data = st.session_state.questions_data

st.markdown("")
st.markdown("")

# ========================================
# STEP 3: CREATE TEST
# ========================================

st.markdown("### Step 3: Create Test")

can_create = all([
    test_title,
    subject,
    duration,
    access_code,
    questions_valid,
    len(questions_data) > 0
])

if not can_create:
    st.info("👆 Please complete Steps 1 and 2 above to enable test creation")
else:
    st.success("✅ Ready to create test!")

create_button = st.button(
    "🚀 Create Test and Generate Link",
    type="primary",
    disabled=not can_create,
    use_container_width=True
)

# 🔒 CREATE ONLY ONCE
if create_button and can_create and not st.session_state.get("test_created"):
    with st.spinner("Creating test..."):
        try:
            expiry_datetime = datetime.combine(
                st.session_state.form_expiry_date,
                st.session_state.form_expiry_time
            )

            test_data = {
                "title": test_title.strip(),
                "subject": subject.strip(),
                "duration": int(duration),
                "expiry_time": expiry_datetime,
                "access_code": st.session_state.form_access_code.strip().upper(),
                "total_questions": len(questions_data),
                "status": "active"
            }

            teacher_id = get_current_user_id()
            test_id = create_test(teacher_id, test_data)

            if not test_id:
                st.error("❌ Failed to create test")
                st.stop()

            questions_created = create_questions_batch(test_id, questions_data)

            if not questions_created:
                st.error("❌ Failed to upload questions")
                st.stop()
        
            # ✅ SUCCESS STATE
            st.session_state.test_created = True
            st.session_state.created_test_id = test_id
            st.session_state.created_access_code = st.session_state.form_access_code
            st.session_state.created_questions_count = len(questions_data)
            st.session_state.created_expiry = expiry_datetime

            st.rerun()

        except Exception as e:
            st.error(f"❌ Error creating test: {str(e)}")
            
# ========================================
# SUCCESS STATE UI
# ========================================

if st.session_state.get("test_created"):
    test_id = st.session_state.created_test_id
    access_code = st.session_state.created_access_code
    expiry_datetime = st.session_state.created_expiry
    questions_count = st.session_state.created_questions_count

    test_link = f"https://rasheedmrandroid-compass.hf.space/take_test?id={test_id}"

    # 🎈 Fire balloons ONCE
    if not st.session_state.get("success_ui_shown"):
        st.balloons()
        st.session_state.success_ui_shown = True

    st.markdown(
        f"""
        <div class="success-box">
            <h3>🎉 Test Created Successfully!</h3>
            <p><strong>Test ID:</strong> <code>{test_id}</code></p>
            <p><strong>Access Code:</strong> <code>{access_code.upper()}</code></p>
            <p><strong>Total Questions:</strong> {questions_count}</p>
            <p><strong>Expires:</strong> {expiry_datetime.strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 📋 Share with Students")
    st.code(test_link)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 View Test Management", use_container_width=True):
            st.session_state.last_page = "view_test"
            st.switch_page("pages/view_test.py")

    with col2:
        if st.button("➕ Create Another Test", use_container_width=True):
            clear_form_state()
            init_form_state()
            st.rerun()

    st.stop()

st.markdown("")
st.caption("Built with ❤️ by Mr. Android for Nigerian tutorial centers | MVP v1.0")