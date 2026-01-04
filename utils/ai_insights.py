"""
AI Insights Generator

This module generates natural language insights using Groq-hosted LLaMA.
Insights are based on aggregated analytics, not raw guesses.
"""

import os
import json
import requests
from typing import Dict, List, Optional
import streamlit as st


class AIInsightsGenerator:
    """
    Generate AI-powered educational insights using Groq API.
    """
    
    def __init__(self):
        """Initialize with Groq API credentials."""
        # Try environment variable first
        self.api_key = os.getenv('GROQ_API_KEY')
        
        # Try Streamlit secrets if env var not found
        if not self.api_key and hasattr(st, 'secrets'):
            try:
                self.api_key = st.secrets.get('GROQ_API_KEY')
            except Exception:
                pass
        
        # Get model name
        self.model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
        if hasattr(st, 'secrets') and not os.getenv('GROQ_MODEL'):
            try:
                self.model = st.secrets.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
            except Exception:
                pass
        
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        if not self.api_key:
            st.warning("⚠️ GROQ_API_KEY not set. AI insights will not be available.")
    
    def _make_api_call(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """
        Make API call to Groq.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
        
        Returns:
            str: AI-generated text or None if error
        """
        if not self.api_key:
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert educational consultant for Nigerian tutorial centers. Provide practical, actionable advice based on test analytics. Be concise, specific, and culturally relevant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
            else:
                st.error(f"Groq API error: {response.status_code}")
                return None
        
        except Exception as e:
            st.error(f"Error generating AI insights: {str(e)}")
            return None
    
    def generate_revision_plan(self, analytics: Dict) -> Optional[str]:
        """
        Generate a revision plan based on test analytics.
        
        Args:
            analytics: Output from generate_comprehensive_analytics()
        
        Returns:
            str: AI-generated revision plan
        """
        if not analytics.get('has_data'):
            return None
        
        # Extract key metrics
        weak_topics = analytics.get('weak_topics', [])
        risk_stats = analytics['risk_classification']['stats']
        readiness = analytics['class_readiness']
        
        # Build context-rich prompt
        prompt = f"""
Based on the following test analytics for a Nigerian tutorial center, create a concise revision plan:

TEST OVERVIEW:
- Total Students: {analytics['total_submissions']}
- Average Score: {readiness['average_percentage']:.1f}%
- Class Readiness: {readiness['status']}

STUDENT RISK DISTRIBUTION:
- High Risk (< 40%): {risk_stats['high_risk_count']} students
- Medium Risk (40-65%): {risk_stats['medium_risk_count']} students
- Low Risk (> 65%): {risk_stats['low_risk_count']} students

WEAK TOPICS (< 60% accuracy):
{chr(10).join(f"- {topic}: {accuracy:.1f}%" for topic, accuracy in weak_topics[:5])}


Provide a practical 3-week revision plan with:
1. Priority topics to focus on immediately
2. Specific teaching strategies for weak areas
3. How to support high-risk students
4. Timeline recommendation for the external exam

Keep it under 400 words, actionable, and specific to Nigerian educational context.
"""
        
        return self._make_api_call(prompt, max_tokens=600)
    
    def generate_student_intervention_advice(
        self,
        student_name: str,
        percentage: float,
        weak_topics: List[str]
    ) -> Optional[str]:
        """
        Generate personalized intervention advice for a student.
        
        Args:
            student_name: Student's name
            percentage: Overall test percentage
            weak_topics: List of topics where student scored < 60%
        
        Returns:
            str: AI-generated advice
        """
        if not self.api_key:
            return None
        
        risk_level = "high" if percentage < 40 else ("medium" if percentage < 65 else "low")
        
        prompt = f"""
A student in a Nigerian tutorial center needs help:

STUDENT: {student_name}
SCORE: {percentage:.1f}%
RISK LEVEL: {risk_level.title()}
WEAK TOPICS: {', '.join(weak_topics) if weak_topics else 'None identified'}

Provide brief, actionable advice (under 200 words):
1. What this student should focus on immediately

2. Specific study techniques for their weak areas

Encouragement tailored to their performance level

Be supportive but honest about the work needed.
"""
        
        return self._make_api_call(prompt, max_tokens=300)
    
    def generate_topic_teaching_tips(self, topic: str, accuracy: float) -> Optional[str]:
        """
        Generate teaching tips for a specific weak topic.
        
        Args:
            topic: Topic name
            accuracy: Current class accuracy for this topic
        
        Returns:
            str: AI-generated teaching tips
        """
        if not self.api_key:
            return None
        
        prompt = f"""
A Nigerian tutorial center class is struggling with:

TOPIC: {topic}
CLASS ACCURACY: {accuracy:.1f}%

This is below expectations. Suggest:
1. Common misconceptions in this topic
2. Teaching approaches that work well for Nigerian students
3. Practice resources or question types to focus on
4. Quick diagnostic to identify specific gaps

Keep it under 250 words, practical and immediately implementable.
"""
        
        return self._make_api_call(prompt, max_tokens=400)
    
    def generate_readiness_assessment(self, analytics: Dict) -> Optional[str]:
        """
        Generate exam readiness assessment and recommendation.
        
        Args:
            analytics: Output from generate_comprehensive_analytics()
        
        Returns:
            str: AI-generated assessment
        """
        if not analytics.get('has_data'):
            return None
        
        readiness = analytics['class_readiness']
        stats = analytics['statistics']
        
        prompt = f"""
Assess exam readiness for a Nigerian tutorial center class:

READINESS SCORE: {readiness['readiness_score']:.1f}/100
STATUS: {readiness['status']}
AVERAGE SCORE: {readiness['average_percentage']:.1f}%
SCORE SPREAD (Std Dev): {readiness['std_deviation']:.1f}%

PERFORMANCE DISTRIBUTION:
- High Performers (≥70%): {readiness['high_performers_pct']:.1f}%
- At Risk (<40%): {readiness['at_risk_pct']:.1f}%

Given these metrics:
1. Should this class proceed to the external exam now?
2. If not, how many weeks of preparation are needed?
3. What are the biggest risks if they take the exam unprepared?
4. What's the realistic target readiness score they should aim for?

Keep it under 300 words, honest and practical.
"""
        
        return self._make_api_call(prompt, max_tokens=400)
    
    def generate_quick_insights(self, analytics: Dict) -> Dict[str, str]:
        """
        Generate multiple quick insights in one call for efficiency.
        
        Args:
            analytics: Output from generate_comprehensive_analytics()
        
        Returns:
            dict: {
                'summary': str,
                'strengths': str,
                'weaknesses': str,
                'action_items': str
            }
        """
        if not analytics.get('has_data') or not self.api_key:
            return {
                'summary': 'AI insights unavailable',
                'strengths': 'Configure GROQ_API_KEY to enable AI insights',
                'weaknesses': 'AI insights require API access',
                'action_items': 'Add your Groq API key to .env file'
            }
        
        weak_topics = analytics.get('weak_topics', [])
        strong_topics = analytics.get('strong_topics', [])
        readiness = analytics['class_readiness']
        risk_stats = analytics['risk_classification']['stats']
        
        prompt = f"""
Provide 4 brief insights (each under 100 words) for this test performance:

METRICS:
- Class Average: {readiness['average_percentage']:.1f}%
- Readiness: {readiness['status']}
- High Risk Students: {risk_stats['high_risk_count']}/{analytics['total_submissions']}
- Top Topics: {', '.join(t[0] for t in strong_topics[:3])}
- Weak Topics: {', '.join(t[0] for t in weak_topics[:3])}

Return ONLY a JSON object with these 4 keys:
{{
    "summary": "One-line summary of overall performance",
    "strengths": "What the class did well",
    "weaknesses": "Key areas of concern",
    "action_items": "Top 3 immediate actions needed"
}}

Ensure valid JSON format.
"""
        
        response = self._make_api_call(prompt, max_tokens=500)
        
        if response:
            try:
                # Try to parse JSON from response
                # Sometimes LLMs add markdown formatting, so strip it
                response_clean = response.strip()
                if response_clean.startswith('```'):
                    # Remove markdown code blocks
                    lines = response_clean.split('\n')
                    response_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_clean
                    response_clean = response_clean.replace('```json', '').replace('```', '')
                
                insights = json.loads(response_clean)
                return insights
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    'summary': response[:200],
                    'strengths': 'See full AI response above',
                    'weaknesses': 'JSON parsing failed',
                    'action_items': 'Review raw response'
                }
        
        return {
            'summary': 'AI insights unavailable',
            'strengths': 'API call failed',
            'weaknesses': 'Check API key and connection',
            'action_items': 'Retry or check logs'
        }


# Global instance
ai_generator = AIInsightsGenerator()


# Convenience functions
def get_revision_plan(analytics: Dict) -> Optional[str]:
    """Wrapper for generating revision plan."""
    return ai_generator.generate_revision_plan(analytics)


def get_student_advice(student_name: str, percentage: float, weak_topics: List[str]) -> Optional[str]:
    """Wrapper for generating student advice."""
    return ai_generator.generate_student_intervention_advice(student_name, percentage, weak_topics)


def get_topic_tips(topic: str, accuracy: float) -> Optional[str]:
    """Wrapper for generating topic teaching tips."""
    return ai_generator.generate_topic_teaching_tips(topic, accuracy)


def get_readiness_assessment(analytics: Dict) -> Optional[str]:
    """Wrapper for generating readiness assessment."""
    return ai_generator.generate_readiness_assessment(analytics)


def get_quick_insights(analytics: Dict) -> Dict[str, str]:
    """Wrapper for generating quick insights."""
    return ai_generator.generate_quick_insights(analytics)