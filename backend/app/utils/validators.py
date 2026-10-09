import re


def validate_password(password: str):
    """Validate password meets minimum security criteria."""
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, None


def validate_email(email: str):
    """Validate email format."""
    if not email:
        return False
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email.strip()))


def validate_pdf_content(text: str):
    """Check if the extracted text has indicators of a medical/laboratory report."""
    if not text or len(text.strip()) < 40:
        return False, "Extracted text is too short to be a valid laboratory report."

    medical_markers = [
        "blood",
        "test",
        "report",
        "lab",
        "laboratory",
        "specimen",
        "reference",
        "result",
        "hemoglobin",
        "wbc",
        "rbc",
        "platelet",
        "glucose",
        "cholesterol",
        "creatinine",
        "alt",
        "ast",
        "urine",
        "panel",
        "profile",
        "patient",
        "clinical",
        "diagnostic",
        "normal",
    ]

    text_lower = text.lower()
    matches = sum(1 for term in medical_markers if term in text_lower)

    if matches < 2:
        return (
            False,
            "The uploaded document does not appear to contain medical or laboratory blood test data. "
            "Please upload a valid blood or lab report.",
        )

    return True, None
