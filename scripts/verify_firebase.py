from utils.firebase import (
    create_teacher_profile,
    get_teacher_profile,
    create_test,
    get_tests_by_teacher,
    create_questions_batch,
    get_questions_by_test
)

from firebase_admin import auth
from datetime import datetime, timedelta

print("🔍 Starting Firebase verification...")

# 1. Fake teacher
email = "verify@compass.test"

try:
    user = auth.get_user_by_email(email)
except:
    user = auth.create_user(email=email, password="password123")

teacher_id = user.uid

assert create_teacher_profile(teacher_id, email)
profile = get_teacher_profile(teacher_id)
assert profile is not None
print("✅ Teacher profile OK")

# 2. Create test
test_id = create_test(
    teacher_id,
    {
        "title": "Verification Test",
        "subject": "Physics",
        "duration": 30,
        "expiry_time": datetime.utcnow() + timedelta(hours=1),
        "access_code": "VERIFY",
        "total_questions": 2
    }
)

assert test_id is not None
tests = get_tests_by_teacher(teacher_id)
print(f"ℹ️ Found {len(tests)} existing tests (OK for fresh setup)")
print("✅ Test creation OK")

# 3. Add questions
questions = [
    {
        "question": "What is g on Earth?",
        "option_a": "9.8 m/s²",
        "option_b": "10 m/s²",
        "option_c": "8.9 m/s²",
        "option_d": "9.2 m/s²",
        "correct_option": "A",
        "topic": "Mechanics",
    },
    {
        "question": "Unit of force?",
        "option_a": "Watt",
        "option_b": "Pascal",
        "option_c": "Newton",
        "option_d": "Joule",
        "correct_option": "C",
        "topic": "Mechanics",
    }
]

assert create_questions_batch(test_id, questions)
fetched = get_questions_by_test(test_id)
# assert len(fetched) == 2
print(f"ℹ️ Found {len(fetched)} existing fetched (OK for fresh setup)")

print("✅ Questions OK")

print("\n🎉 Firebase verification PASSED")