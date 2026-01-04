"""
Exam Interface Page

This page handles:
- Display questions one at a time
- Timer countdown
- Answer selection and saving
- Navigation (next, previous)
- Progress tracking
- Submission (manual and auto)
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta, timezone
import time
from utils.firebase import get_questions_by_test, get_test_by_id, create_submission

# Page configuration
st.set_page_config(
    page_title="Exam in Progress - comPASS",
    page_icon="⏱️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .timer-box {
        position: fixed;
        top: 80px;
        right: 20px;
        background: #fff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        z-index: 999;
        min-width: 150px;
    }
            
    .timer-normal {
        background: #f8f9fa;
        border-radius: 14px;
        padding: 1.2rem;
        text-align: center;
    }
    
    .timer-critical {
        background: #f8d7da !important;
        border: 2px solid #dc3545;
    }
    
    .timer-warning {
        background: #fff3cd !important;
        border: 2px solid #ffc107;
    }
            
    .timer-danger {
        background: #f8d7da;
        border-radius: 14px;
        padding: 1.2rem;
        text-align: center;
    }
    
    /* STRICT question card targeting */
    div[data-testid="stVerticalBlock"]:has(> div > .question-anchor) {
        background: white;
        border-radius: 14px;
        padding: 2rem;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        margin-bottom: 1.5rem;
    }



    .question-meta {
        font-size: 0.85rem;
        color: #555;
    }
    
    .progress-bar {
        background: #e9ecef;
        height: 8px;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    .progress-fill {
        background: #28a745;
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s;
    }
    
    @media (max-width: 768px) {
        .timer-box {
            position: static;
            width: 100%;
            margin-bottom: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ========================================
# CHECK TEST SESSION
# ========================================

if 'test_session' not in st.session_state:
    st.error("❌ No active test session")
    st.markdown("""
    ### Session Not Found
    
    Please start the test from the access page.
    """)
    if st.button("🔙 Go to Test Access", use_container_width=True):
        st.switch_page("pages/take_test.py")
    st.stop()

session = st.session_state.test_session
test_id = session['test_id']

# ========================================
# LOAD TEST AND QUESTIONS
# ========================================

# Load questions (cache in session state)
if 'questions' not in session:
    with st.spinner("Loading questions..."):
        questions = get_questions_by_test(test_id)
        if not questions:
            st.error("❌ No questions found for this test")
            st.stop()
        session['questions'] = questions

questions = session['questions']
total_questions = len(questions)

# ========================================
# TIMER CALCULATION
# ========================================

start_time = session['start_time']
duration_seconds = session['duration'] * 60
end_time = start_time + timedelta(seconds=duration_seconds)
time_remaining = (end_time - datetime.now(timezone.utc)).total_seconds()

# Check if time has expired
if time_remaining <= 0:
    st.warning("⏰ Time's up! Submitting your test...")
    # Auto-submit
    st.switch_page("pages/submit_test.py")
    st.stop()

# Timer status
timer_class = "timer-box"
if time_remaining < 60:  # Last minute - critical
    timer_class = "timer-box timer-critical"
elif time_remaining < 300:  # Last 5 minutes - warning
    timer_class = "timer-box timer-warning"

# Format time remaining
minutes = int(time_remaining // 60)
seconds = int(time_remaining % 60)

# ========================================
# HEADER WITH TIMER
# ========================================

col1, col2 = st.columns([3, 1])

with col1:
    st.title(f"📝 {session['test_title']}")
    st.markdown(f"**Subject:** {session['test_subject']} | **Student:** {session['student_name']}")

with col2:
    if time_remaining < 60:
        timer_html = f"""
        <div class="{timer_class}">
            <h3>⏰ {minutes}:{seconds:02d}</h3>
            <strong style="color:#dc3545;">TIME CRITICAL!</strong>
        </div>
        """
    elif time_remaining < 300:
        timer_html = f"""
        <div class="{timer_class}">
            <h3>⏱️ {minutes}:{seconds:02d}</h3>
            <strong style="color:#ffc107;">5 min remaining</strong>
        </div>
        """
    else:
        timer_html = f"""
        <div class="{timer_class}">
            <h3>⏱️ {minutes}:{seconds:02d}</h3>
            <span>Time Remaining</span>
        </div>
        """

    st.markdown(timer_html, unsafe_allow_html=True)

st.markdown("")
st.markdown("")

# ========================================
# PROGRESS BAR
# ========================================

answered_count = len(session['answers'])
progress_percentage = (answered_count / total_questions) * 100

st.markdown(f"**Progress:** {answered_count}/{total_questions} questions answered ({progress_percentage:.0f}%)")

st.markdown(f"""
<div class="progress-bar">
    <div class="progress-fill" style="width: {progress_percentage}%"></div>
</div>
""", unsafe_allow_html=True)

st.markdown("")
st.markdown("")

# ========================================
# CURRENT QUESTION
# ========================================

current_idx = session['current_question']
current_question = questions[current_idx]
question_id = current_question['id']

# Mark as visited
session['visited_questions'].add(question_id)

# =========================
# QUESTION CARD (CORRECT)
# =========================
with st.container():
    # anchor div for CSS targeting
    st.markdown('<div class="question-anchor"></div>', unsafe_allow_html=True)

    st.markdown(f"### Question {current_idx + 1} of {total_questions}")

    st.divider()


    st.markdown(
        f"<div class='question-meta'><strong>Topic:</strong> {current_question['topic']}</div>",
        unsafe_allow_html=True
        )

    # st.divider()
    # st.markdown("")
    st.markdown("")

    st.markdown(f"### {current_question['question']}")

    options = {
        'A': current_question['option_a'],
        'B': current_question['option_b'],
        'C': current_question['option_c'],
        'D': current_question['option_d']
    }

    current_answer = session['answers'].get(question_id)

    selected_option = st.radio(
        "Select your answer:",
        options=list(options.keys()),
        format_func=lambda x: f"{x}. {options[x]}",
        index=list(options.keys()).index(current_answer) if current_answer else None,
        key=f"question_{question_id}"
    )

    if selected_option:
        session['answers'][question_id] = selected_option

st.markdown("")
st.markdown("")

# ========================================
# NAVIGATION BUTTONS
# ========================================

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if current_idx > 0:
        if st.button("⬅️ Previous", use_container_width=True):
            session['current_question'] = current_idx - 1
            st.rerun()
    else:
        st.button("⬅️ Previous", use_container_width=True, disabled=True)

with col2:
    if current_idx < total_questions - 1:
        if st.button("Next ➡️", use_container_width=True, type="primary"):
            session['current_question'] = current_idx + 1
            st.rerun()
    else:
        st.button("Next ➡️", use_container_width=True, disabled=True)

with col3:
    # Submit button (always available)
    if st.button("✅ Submit Test", use_container_width=True, type="primary"):
        st.switch_page("pages/submit_test.py")

st.markdown("")
st.markdown("")

# ========================================
# QUESTION NAVIGATOR
# ========================================

with st.expander("🗺️ Question Navigator"):
    st.markdown("**Jump to any question:**")
    
    # Create grid of question buttons
    cols = st.columns(10)
    
    for idx, question in enumerate(questions):
        col_idx = idx % 10
        with cols[col_idx]:
            q_id = question['id']
            
            # Determine button style
            if q_id in session['answers']:
                button_label = f"✅ {idx + 1}"
                button_type = "secondary"
            elif q_id in session['visited_questions']:
                button_label = f"👁️ {idx + 1}"
                button_type = "secondary"
            else:
                button_label = f"⭕ {idx + 1}"
                button_type = "secondary"
            
            if idx == current_idx:
                button_label = f"➡️ {idx + 1}"
            
            if st.button(button_label, key=f"nav_{idx}", use_container_width=True):
                session['current_question'] = idx
                st.rerun()
    
    st.markdown("")
    st.markdown("")
    st.markdown("""
    **Legend:**
    - ✅ Answered
    - 👁️ Visited but not answered
    - ⭕ Not visited
    - ➡️ Current question
    """)

# ========================================
# WARNINGS AND REMINDERS
# ========================================

# if answered_count < total_questions:
#     unanswered = total_questions - answered_count
#     if unanswered > 0:
#         st.info(f"💡 You have {unanswered} unanswered question(s). Use the question navigator to review.")

# if time_remaining < 300 and answered_count < total_questions:
#     st.warning(f"⚠️ Only {minutes} minutes remaining! You have {total_questions - answered_count} unanswered questions.")

# ========================================
# AUTO-REFRESH FOR TIMER
# ========================================

# Rerun every second to update timer
st_autorefresh(interval=1000, key="exam_timer")
# st.rerun()

st.caption("comPASS v1.0 | Exam Interface")