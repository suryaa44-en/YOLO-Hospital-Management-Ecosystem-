import random

def generate_patient_uid():
    """Generates a random 11-digit patient UID."""
    return random.randint(100_000_000_00, 999_999_999_99)
