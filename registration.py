from datetime import datetime
import secrets
import string

OFFICE_CODE = "0810400"


def generate_registration_number():
    year = datetime.now().year

    digits = string.digits
    serial = "".join(secrets.choice(digits) for _ in range(13))

    return f"{OFFICE_CODE}{serial} / {year}"
