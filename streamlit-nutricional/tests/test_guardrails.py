from guardrails import Guard
from guardrails.errors import ValidationError
from guardrails.hub import RestrictToTopic

# Setup Guard
guard = Guard().use(
    RestrictToTopic(
        valid_topics=["sports"],
        invalid_topics=["music"],
        disable_classifier=True,
        disable_llm=False,
        on_fail="exception"
    )
)

def validate_text(text):
    try:
        guard.validate(text)
        print("Validation passed.")
    except ValidationError as e:
        print(f"Validation failed: {e}")

# Test cases
validate_text("""
In Super Bowl LVII in 2023, the Chiefs clashed with the Philadelphia Eagles in a fiercely contested battle, ultimately emerging victorious with a score of 38-35.
""")  # Validator passes

validate_text("""
The Beatles were a charismatic English pop-rock band of the 1960s.
""")  # Validator fails