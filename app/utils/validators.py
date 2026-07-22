from string import ascii_lowercase, ascii_uppercase, digits, punctuation
import re


def validate_password(password: str) -> None:
    """Validate password policy and raise ValueError on invalid input.

    Policy (docs/05): min 12 chars, at least 1 upper, 1 lower, 1 digit, 1 special.
    """
    if not isinstance(password, str) or not password:
        raise ValueError("პაროლი სავალდებულოა.")

    if len(password) < 12:
        raise ValueError("პაროლი უნდა იყოს მინიმუმ 12 სიმბოლო.")

    contains_uppercase = False
    contains_lowercase = False
    contains_digits = False
    contains_special = False
    allowed_characters = set(ascii_lowercase + ascii_uppercase + digits + punctuation)

    for character in password:
        if character not in allowed_characters:
            raise ValueError(
                "პაროლი შეიძლება შეიცავდეს მხოლოდ ინგლისურ ასოებს, ციფრებს და სიმბოლოებს !@#$%^&*"
            )
        if character in ascii_uppercase:
            contains_uppercase = True
        elif character in ascii_lowercase:
            contains_lowercase = True
        elif character in digits:
            contains_digits = True
        elif character in punctuation:
            contains_special = True

    if not contains_uppercase:
        raise ValueError("პაროლი უნდა შეიცავდეს მინიმუმ ერთ დიდ ასოს.")
    if not contains_lowercase:
        raise ValueError("პაროლი უნდა შეიცავდეს მინიმუმ ერთ პატარა ასოს.")
    if not contains_digits:
        raise ValueError("პაროლი უნდა შეიცავდეს მინიმუმ ერთ ციფრს.")
    if not contains_special:
        raise ValueError("პაროლი უნდა შეიცავდეს მინიმუმ ერთ სპეციალურ სიმბოლოს.")


def normalize_ge_phone(phone: str) -> str:
    """
    Validate and normalize Georgian phone number to E.164: +9955XXXXXXXX.
    - Must start with +995
    - Remaining part must be digits only
    """
    if not isinstance(phone, str) or not phone.strip():
        raise ValueError("ტელეფონის ნომერი სავალდებულოა.")

    # Basic cleanup for user input convenience.
    normalized = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not normalized.startswith("+995"):
        raise ValueError("ტელეფონის ნომერი უნდა იწყებოდეს +995-ით.")

    local = normalized[4:]
    if not local.isdigit():
        raise ValueError("ტელეფონის ნომრის +995-ის შემდეგ ნაწილი უნდა იყოს მხოლოდ ციფრები.")

    if len(local) != 9 or not local.startswith("5"):
        raise ValueError("ტელეფონის ნომერი უნდა იყოს ფორმატში: +9955XXXXXXXX.")

    return f"+995{local}"


def normalize_email(email: str) -> str:
    """Validate and normalize email value."""
    if not isinstance(email, str) or not email.strip():
        raise ValueError("ელ.ფოსტა სავალდებულოა.")

    normalized = email.strip().lower()
    email_pattern = r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
    if not re.fullmatch(email_pattern, normalized):
        raise ValueError("ელ.ფოსტის ფორმატი არასწორია.")

    return normalized