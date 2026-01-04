"""
Test Management Page
This page displays:
- List of all tests created by the teacher
- Test status (active/expired)
- Number of submissions per test
- Actions: View analytics, Download report, View details
"""
import streamlit as st
from datetime import datetime, timezone
import pandas as pd
from utils.auth import require_authentication, get_current_user_id, get_user_display_name
from utils.firebase import get_tests_by_teacher, get_submission_count, get_test_by_id
import streamlit.components.v1 as components

# Protect this page - require login
require_authentication()

# Page configuration
st.set_page_config(
    page_title="My Tests - comPASS",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ========================================
# HEADER
# ========================================

st.title("📚 My Tests")
teacher_name = get_user_display_name()
st.markdown(f"**Welcome back, {teacher_name}!**")

st.markdown("")
st.markdown("")

# ========================================
# ACTION BUTTONS
# ========================================

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    if st.button("➕ Create New Test", use_container_width=True, type="primary"):
        st.session_state.last_visited_page = "create_test"
        st.switch_page("pages/create_test.py")

with col2:
    if st.button("📊 View Dashboard", use_container_width=True):
        st.switch_page("pages/dashboard.py")

with col3:
    refresh = st.button("🔄 Refresh", use_container_width=True)

st.markdown("")
st.markdown("")

# ========================================
# FETCH TESTS
# ========================================

teacher_id = get_current_user_id()

with st.spinner("Loading your tests..."):
    tests = get_tests_by_teacher(teacher_id)

if not tests:
    st.info("📭 No tests created yet")
    st.markdown("""
    ### Get Started!
    
    Click the **"Create New Test"** button above to:
    1. Upload questions via CSV
    2. Set test parameters
    3. Generate a shareable test link
    4. Start collecting student responses
    """)
    st.stop()

# ========================================
# STATISTICS OVERVIEW
# ========================================

st.markdown("### 📊 Overview")

total_tests = len(tests)
now = datetime.now(timezone.utc)
active_tests = 0
expired_tests = 0

# Check expiry dynamically
for t in tests:
    expiry = t.get("expiry_time")
    if isinstance(expiry, datetime):
        # Make expiry timezone-aware if it isn't already
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        
        if now > expiry:
            expired_tests += 1
        else:
            active_tests += 1
    else:
        # If no expiry time, consider it active
        active_tests += 1

total_submissions = sum(get_submission_count(t['id']) for t in tests)

st.markdown(f"""
<style>
.metric-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
}}
.metric-box {{
    background: white;
    border-radius: 14px;
    padding: 1.5rem 1.2rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    text-align: center;
    border: 1px solid #dee2e6;
}}
.metric-title {{
    font-size: 0.85rem;
    color: #666;
    margin-bottom: 0.4rem;
    font-weight: 500;
}}
.metric-value {{
    font-size: 2rem;
    font-weight: 700;
    color: #111;
    margin: 0;
}}
</style>
<div class="metric-grid">
    <div class="metric-box">
        <div class="metric-title">Total Tests</div>
        <div class="metric-value">{total_tests}</div>
    </div>
    <div class="metric-box">
        <div class="metric-title">Active Tests</div>
        <div class="metric-value">{active_tests}</div>
    </div>
    <div class="metric-box">
        <div class="metric-title">Expired Tests</div>
        <div class="metric-value">{expired_tests}</div>
    </div>
    <div class="metric-box">
        <div class="metric-title">Total Submissions</div>
        <div class="metric-value">{total_submissions}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")
st.markdown("")

# ========================================
# FILTER & SORT OPTIONS
# ========================================

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    filter_status = st.selectbox(
        "Filter by Status",
        ["All", "Active", "Expired"],
        key="filter_status"
    )

with col2:
    sort_by = st.selectbox(
        "Sort by",
        ["Most Recent", "Oldest First", "Most Submissions", "Title (A-Z)"],
        key="sort_by"
    )

with col3:
    view_mode = st.radio(
        "View",
        ["Cards", "Table"],
        horizontal=True,
        key="view_mode"
    )

st.markdown("")
st.markdown("")

# ========================================
# HELPER FUNCTION TO CHECK IF TEST IS EXPIRED
# ========================================

def is_test_expired(test):
    """Check if a test is expired based on expiry_time"""
    expiry = test.get("expiry_time")
    if isinstance(expiry, datetime):
        # Make timezone-aware if needed
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expiry
    return False

# ========================================
# FILTER AND SORT TESTS
# ========================================

# Apply status filter based on ACTUAL expiry time, not stored status
if filter_status == "Active":
    filtered_tests = [t for t in tests if not is_test_expired(t)]
elif filter_status == "Expired":
    filtered_tests = [t for t in tests if is_test_expired(t)]
else:
    filtered_tests = tests

# Apply sorting
if sort_by == "Most Recent":
    filtered_tests.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
elif sort_by == "Oldest First":
    filtered_tests.sort(key=lambda x: x.get('created_at', datetime.min))
elif sort_by == "Most Submissions":
    filtered_tests.sort(key=lambda x: get_submission_count(x['id']), reverse=True)
elif sort_by == "Title (A-Z)":
    filtered_tests.sort(key=lambda x: x.get('title', ''))

# ========================================
# DISPLAY TESTS
# ========================================

if not filtered_tests:
    st.info(f"No {filter_status.lower()} tests found")
else:
    st.markdown(f"### Showing {len(filtered_tests)} test(s)")      
    if view_mode == "Cards":
        for test in filtered_tests:
            submission_count = get_submission_count(test["id"])
            expiry = test.get("expiry_time")
            
            # Format expiry date
            expiry_str = (
                expiry.strftime("%b %d, %Y")
                if isinstance(expiry, datetime)
                else "N/A"
            )
            
            # Determine status dynamically
            is_expired = is_test_expired(test)
            status = "EXPIRED" if is_expired else "ACTIVE"
            status_color = "#28a745" if status == "ACTIVE" else "#dc3545"
            
            test_link = f"https://rasheedmrandroid-compass.hf.space/take_test?id={test['id']}"
        # Add card styles
        st.markdown("""
        <style>
        .test-card {
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 14px rgba(0,0,0,0.06);
            font-family: Inter, system-ui, sans-serif;
            border: 1px solid #e0e0e0;
        }
        .test-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .test-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #111;
        }
        .status {
            font-weight: 600;
            font-size: 0.9rem;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
        }
        .status-active {
            color: #28a745;
            background: #d4edda;
        }
        .status-expired {
            color: #dc3545;
            background: #f8d7da;
        }
        .test-meta {
            font-size: 0.9rem;
            color: #555;
            margin-bottom: 1.2rem;
        }
        .test-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 1rem;
            margin-bottom: 1.2rem;
        }
        .meta-box {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 0.8rem;
            text-align: center;
            font-size: 0.85rem;
            border: 1px solid #dee2e6;
        }
        .meta-box strong {
            display: block;
            font-size: 1rem;
            margin-top: 0.2rem;
            color: #111;
        }
        </style>
        """, unsafe_allow_html=True)
        
        for test in filtered_tests:
            submission_count = get_submission_count(test["id"])
            expiry = test.get("expiry_time")
            
            # Format expiry date
            expiry_str = (
                expiry.strftime("%b %d, %Y")
                if isinstance(expiry, datetime)
                else "N/A"
            )
            
            # Determine status dynamically
            is_expired = is_test_expired(test)
            status = "EXPIRED" if is_expired else "ACTIVE"
            status_class = "status-active" if status == "ACTIVE" else "status-expired"
            
            test_link = f"https://rasheedmrandroid-compass.hf.space/take_test?id={test['id']}"
            
            st.markdown(f"""
            <div class="test-card">
                <div class="test-header">
                    <div class="test-title">{test['title']}</div>
                    <div class="status {status_class}">● {status}</div>
                </div>
                <div class="test-meta">
                    {test['subject']} • {test['total_questions']} Questions
                </div>
                <div class="test-grid">
                    <div class="meta-box">
                        Duration
                        <strong>{test['duration']} min</strong>
                    </div>
                    <div class="meta-box">
                        Access Code
                        <strong>{test['access_code']}</strong>
                    </div>
                    <div class="meta-box">
                        Submissions
                        <strong>{submission_count}</strong>
                    </div>
                    <div class="meta-box">
                        Expires
                        <strong>{expiry_str}</strong>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons (Streamlit handles these)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 View Analytics", key=f"analytics_{test['id']}", use_container_width=True):
                    st.session_state.selected_test_id = test["id"]
                    st.switch_page("pages/dashboard.py")
            
            with col2:
                if st.button("📄 Download Report", key=f"report_{test['id']}", use_container_width=True):
                    submission_count = get_submission_count(test['id'])
                    if submission_count == 0:
                        st.warning("⚠️ No submissions yet. Report will be empty.")
                    else:
                        with st.spinner("Generating report..."):
                            from utils.firebase import get_questions_by_test, get_submissions_by_test
                            from utils.analytics import generate_comprehensive_analytics
                            from utils.ai_insights import get_quick_insights
                            from utils.html_report_generator import generate_html_report
                            from datetime import datetime
                            
                            try:
                                questions = get_questions_by_test(test['id'])
                                submissions = get_submissions_by_test(test['id'])
                                analytics = generate_comprehensive_analytics(questions, submissions)
                                ai_insights = get_quick_insights(analytics)
                                
                                html_report = generate_html_report(
                                    test_title=test['title'],
                                    test_subject=test['subject'],
                                    analytics=analytics,
                                    ai_insights=ai_insights
                                )
                                
                                st.download_button(
                                    label="⬇️ Download HTML",
                                    data=html_report,
                                    file_name=f"Report_{test['title'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html",
                                    mime="text/html",
                                    key=f"download_card_{test['id']}"
                                )
                                st.success("✅ Report ready!")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            
            with col3:
                if st.button("🔗 Copy Test Link", key=f"link_{test['id']}", use_container_width=True):
                    st.code(test_link, language=None)
            
            st.markdown("")
            st.markdown("")
    
    else:
        # ========================================
        # TABLE VIEW
        # ========================================
        table_data = []
        
        for test in filtered_tests:
            submission_count = get_submission_count(test["id"])
            expiry = test.get("expiry_time")
            
            # Determine status dynamically
            is_expired = is_test_expired(test)
            status = "EXPIRED" if is_expired else "ACTIVE"
            
            expiry_str = (
                expiry.strftime("%Y-%m-%d %H:%M")
                if isinstance(expiry, datetime)
                else "N/A"
            )
            
            table_data.append({
                "Title": test["title"],
                "Subject": test["subject"],
                "Questions": test["total_questions"],
                "Duration (min)": test["duration"],
                "Access Code": test["access_code"],
                "Status": status,
                "Submissions": submission_count,
                "Expires": expiry_str,
                "Test ID": test["id"],
            })
        
        df = pd.DataFrame(table_data)
        
        # ---- Style the dataframe ----
        def highlight_status(val):
            if val == "ACTIVE":
                return "background-color: #d4edda; color: #155724"
            elif val == "EXPIRED":
                return "background-color: #f8d7da; color: #721c24"
            return ""
        
        styled_df = df.style.applymap(highlight_status, subset=["Status"])
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        st.markdown("")
        st.markdown("")
        
        # ========================================
        # DETAILED VIEW
        # ========================================
        
        st.markdown("### View Test Details")
        
        test_ids = [t["id"] for t in filtered_tests]
        test_titles = {t["id"]: t["title"] for t in filtered_tests}
        
        selected_test = st.selectbox(
            "Select a test to view details",
            options=test_ids,
            format_func=lambda x: test_titles[x],
            key="selected_test_details",
        )
        
        if selected_test:
            test = get_test_by_id(selected_test)
            
            if test:
                # Determine status dynamically
                is_expired = is_test_expired(test)
                status = "EXPIRED" if is_expired else "ACTIVE"
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Test Information")
                    st.markdown(f"**Title:** {test['title']}")
                    st.markdown(f"**Subject:** {test['subject']}")
                    st.markdown(f"**Questions:** {test['total_questions']}")
                    st.markdown(f"**Duration:** {test['duration']} minutes")
                    st.markdown(f"**Status:** {status}")
                
                with col2:
                    st.markdown("#### Access Information")
                    st.markdown(f"**Access Code:** `{test['access_code']}`")
                    st.markdown(f"**Submissions:** {get_submission_count(test['id'])}")
                    
                    expiry = test.get("expiry_time")
                    if isinstance(expiry, datetime):
                        st.markdown(
                            f"**Expires:** {expiry.strftime('%B %d, %Y at %I:%M %p')}"
                        )
                    
                    test_link = f"https://rasheedmrandroid-compass.hf.space/take_test?id={test['id']}"
                    st.markdown("**Test Link:**")
                    st.code(test_link, language=None)
                
                # Action buttons for selected test
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📊 View Analytics for This Test", use_container_width=True, type="primary"):
                        st.session_state.selected_test_id = test['id']
                        st.switch_page("pages/dashboard.py")
                
                with col2:
                    if st.button("📄 Download Report for This Test", use_container_width=True):
                        submission_count = get_submission_count(test['id'])
                        if submission_count == 0:
                            st.warning("⚠️ No submissions yet. Report will be empty.")
                        else:
                            with st.spinner("Generating report..."):
                                from utils.firebase import get_questions_by_test, get_submissions_by_test
                                from utils.analytics import generate_comprehensive_analytics
                                from utils.ai_insights import get_quick_insights, get_revision_plan
                                from utils.report_generator import generate_test_report
                                from datetime import datetime
                                
                                try:
                                    questions = get_questions_by_test(test['id'])
                                    submissions = get_submissions_by_test(test['id'])
                                    analytics = generate_comprehensive_analytics(questions, submissions)
                                    ai_insights = get_quick_insights(analytics)
                                    revision_plan = get_revision_plan(analytics)
                                    
                                    pdf_buffer = generate_test_report(
                                        test_title=test['title'],
                                        test_subject=test['subject'],
                                        analytics=analytics,
                                        ai_insights=ai_insights,
                                        revision_plan=revision_plan
                                    )
                                    
                                    st.download_button(
                                        label="⬇️ Download PDF",
                                        data=pdf_buffer,
                                        file_name=f"comPASS_Report_{test['title'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                        mime="application/pdf",
                                        key=f"download_selected_{test['id']}"
                                    )
                                    st.success("✅ Report ready!")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")

st.markdown("")
st.markdown("")

# ========================================
# FOOTER
# ========================================

with st.expander("💡 Tips"):
    st.markdown("""
    **Managing Your Tests:**
    - Active tests can still receive submissions
    - Expired tests are automatically closed after the expiry time
    - Click "View Analytics" once students have submitted responses
    - Share both the test link AND access code with students
    
    **Best Practices:**
    - Set realistic expiry times (consider your students' schedules)
    - Use descriptive test titles for easy identification
    - Check submission counts regularly to monitor participation
    - Download reports for detailed performance insights
    """)

st.caption("Built with ❤️ by Mr. Android for Nigerian tutorial centers | MVP v1.0")