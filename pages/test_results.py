"""
Student Test Results Page

This page displays:
- Overall score and percentage
- Topic-wise performance
- Weak topics identification
- AI-generated improvement advice (Phase 6)
- Time taken
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Test Results - comPASS",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
/* ===============================
   RESULT / INSIGHT CARD FIX
   =============================== */

/* Style the container itself */
.result-card {
    background: white;
    padding: 2rem;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    margin: 1.5rem 0;
}

/* Score color modifiers */
.score-excellent { border-left: 6px solid #28a745; background: #d4edda; }
.score-good { border-left: 6px solid #17a2b8; background: #d1ecf1; }
.score-average { border-left: 6px solid #ffc107; background: #fff3cd; }
.score-poor { border-left: 6px solid #dc3545; background: #f8d7da; }

/* Metric block */
.metric-large {
    text-align: center;
    padding: 1.5rem;
}

.metric-large h1 {
    font-size: 3.5rem;
    margin: 0;
}

.result-content {
    display: flex;                 /* side by side */
    gap: 2rem;
    align-items: right;           /* vertical alignment */
}

/* Left block */
.metric-large {
    text-align: center;              /* left aligned content */
    min-width: 160px;
}

/* Right block (message) */
.result-content > div:last-child {
    text-align: left;             /* right aligned text */
    flex: 1;                       /* take remaining space */
}

/* AI Insight card */
.insight-card {
    background: #e7f3ff;
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 5px solid #0066cc;
    ont-family: system-ui, -apple-system, sans-serif;
    line-height: 1.6;
    font-weight: 400;              /* NORMAL text */
    color: #1f2937;                /* softer dark */
}
            
.insight-card strong {
    font-weight: 300;              /* not 700 */
}

.insight-card br {
    margin-bottom: 0.5rem;
}

</style>
""", unsafe_allow_html=True)

# ========================================
# CHECK TEST SESSION
# ========================================

if 'test_session' not in st.session_state or not st.session_state.test_session.get('submitted'):
    st.error("❌ No test results available")
    st.markdown("""
    ### No Results Found
    
    Please complete a test first to view your results.
    """)
    st.stop()

session = st.session_state.test_session

# ========================================
# HEADER
# ========================================

st.title("🎯 Your Test Results")
st.markdown(f"### {session['test_title']}")
st.markdown(f"**Student:** {session['student_name']}")

st.markdown("")

# ========================================
# OVERALL SCORE
# ========================================

score = session['score']
total = session['total_questions']
percentage = session['percentage']

# Determine score category
if percentage >= 80:
    score_class = "score-excellent"
    emoji = "🏆"
    message = "Excellent Performance!"
elif percentage >= 65:
    score_class = "score-good"
    emoji = "👍"
    message = "Good Job!"
elif percentage >= 50:
    score_class = "score-average"
    emoji = "📈"
    message = "Fair Performance"
else:
    score_class = "score-poor"
    emoji = "📉"
    message = "Needs Improvement"

# ========================================
# RESULT CARD
# ========================================
st.markdown(
    f"""
    <div class="result-card {score_class}">
        <div class="result-content">
            <div class="metric-large">
            <h1 style="font-size: 3.5rem; margin: 0; padding: 0">{emoji}</h1>
            <h1 style="font-size: 1.5rem; margin: 0;">{message}</h1>
            <h1 style="font-size: 2.5rem; margin: 0.5rem 0;">{percentage:.1f}%</h1>
            <h3 style="font-size: 1.5rem; margin: 0; padding: 0">{score}/{total}</h3>
            <p><strong>Time Taken:</strong> {session.get('time_taken', 0) // 60} minutes
            {session.get('time_taken', 0) % 60} seconds</p>

    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("")
st.markdown("")

# ========================================
# TOPIC-WISE PERFORMANCE
# ========================================

st.markdown("### 📊 Topic-Wise Performance")

topic_scores = session.get('topic_scores', {})

if topic_scores:
    # Prepare data for display
    topic_data = []
    weak_topics = []
    
    for topic, scores in topic_scores.items():
        correct = scores['correct']
        total_q = scores['total']
        topic_pct = (correct / total_q * 100) if total_q > 0 else 0
        
        topic_data.append({
            'Topic': topic,
            'Correct': correct,
            'Total': total_q,
            'Percentage': topic_pct,
            'Status': '✅ Strong' if topic_pct >= 70 else ('⚠️ Average' if topic_pct >= 50 else '❌ Weak')
        })
        
        # Identify weak topics (< 60%)
        if topic_pct < 60:
            weak_topics.append(topic)
    
    # Sort by percentage descending
    topic_data.sort(key=lambda x: x['Percentage'], reverse=True)
    
    # Display as dataframe
    df = pd.DataFrame(topic_data)
    
    # Format percentage
    df['Percentage'] = df['Percentage'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("")
    st.markdown("")
    
    # ========================================
    # WEAK TOPICS IDENTIFICATION
    # ========================================
    
    if weak_topics:
        st.markdown("### 🎯 Topics That Need Attention")
        
        st.warning(f"You scored below 60% in the following topic(s):")
        
        for topic in weak_topics:
            topic_info = topic_scores[topic]
            st.markdown(f"- **{topic}**: {topic_info['correct']}/{topic_info['total']} correct ({(topic_info['correct']/topic_info['total']*100):.1f}%)")
    else:
        st.success("✅ Great job! You performed well across all topics!")
    
    st.markdown("")
    st.markdown("")

# ========================================
# AI-POWERED PERSONALIZED INSIGHTS
# ========================================

st.markdown("### 🤖 AI-Powered Personalized Advice")

# Identify weak topics for this student
student_weak_topics = [topic for topic, scores in topic_scores.items() 
                        if (scores['correct'] / scores['total'] * 100) < 60] if topic_scores else []

with st.spinner("Generating personalized advice..."):
    from utils.ai_insights import get_student_advice
    
    ai_advice = get_student_advice(
        student_name=session['student_name'],
        percentage=percentage,
        weak_topics=student_weak_topics
    )
    
    if ai_advice:
        # Escape HTML and convert markdown to basic HTML
        advice_html = ai_advice.replace('\n', '<br/>').replace('**', '<strong>')
        
        st.markdown(
            f"""
            <div class="insight-card">
                {advice_html}
            </div>
            """,
            unsafe_allow_html=True
        )
        
    else:
        # Fallback advice if AI is unavailable
        if percentage >= 80:
            fallback = """
            <strong>Great work!</strong> Your performance indicates strong understanding.<br/><br/>
            To maintain this level:<br/>
            • Keep practicing regularly<br/>
            • Review challenging concepts periodically<br/>
            • Help other students to reinforce your knowledge
            """
        elif percentage >= 65:
            fallback = """
            <strong>Good effort!</strong> You have a solid foundation.<br/><br/>
            To improve further:<br/>
            • Focus on the weak topics identified above<br/>
            • Practice more questions in those areas<br/>
            • Seek clarification on confusing concepts
            """
        elif percentage >= 50:
            fallback = """
            <strong>You're on the right track,</strong> but there's room for improvement.<br/><br/>
            Action plan:<br/>
            • Dedicate extra time to weak topics<br/>
            • Break down complex topics into smaller parts<br/>
            • Use multiple study resources<br/>
            • Practice regularly
            """
        else:
            fallback = """
            <strong>Immediate attention needed.</strong> Your score indicates gaps in understanding.<br/><br/>
            Urgent action plan:<br/>
            • Speak with your teacher immediately<br/>
            • Create a structured revision schedule<br/>
            • Focus on fundamentals first<br/>
            • Consider additional tutoring or study groups<br/>
            • Don't be discouraged - consistent effort will improve your scores
            """
        
        components.html(
            f"""
            <style>
            .insight-card {{
                background: #e7f3ff;
                padding: 1.5rem;
                border-radius: 12px;
                border-left: 5px solid #0066cc;
                font-family: system-ui, -apple-system, sans-serif;
                line-height: 1.6;
            }}
            </style>
            <div class="insight-card">
                {fallback}
            </div>
            """,
            height=400
        )

# ========================================
# NEXT STEPS
# ========================================

st.markdown("### 📚 Next Steps")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **For You:**
    1. Review your weak topics
    2. Practice more questions
    3. Seek help if needed
    4. Track your improvement
    """)

with col2:
    st.markdown("""
    **Your Teacher Will:**
    - Review class performance
    - Adjust lesson plans
    - Provide targeted support
    """)

st.markdown("")
st.markdown("")

# ========================================
# FOOTER
# ========================================

if st.button("✅ Done - Close Results", use_container_width=True, type="primary"):
    # Clear test session
    del st.session_state.test_session
    st.success("Session cleared. Thank you for taking the test!")
    st.balloons()

st.markdown("")
st.markdown("")

with st.expander("❓ Have Questions About Your Results?"):
    st.markdown("""
    **Understanding Your Score:**
    - Your percentage is calculated based on correct answers
    - Each question carries equal weight
    - There is no negative marking
    
    **Topic Performance:**
    - Shows your strength in each subject area
    - Weak topics are those where you scored below 60%
    
    **What to Do Next:**
    - Focus on identified weak topics
    - Ask your teacher for guidance
    - Keep practicing and improving
    
    **Privacy:**
    - Only your teacher can see your results
    - Other students cannot access your performance data
    """)

st.caption("comPASS v1.0 | Student Results")