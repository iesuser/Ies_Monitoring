from string import ascii_lowercase, ascii_uppercase, digits, punctuation


def validate_password(password: str) -> None:
    """Validate password policy and raise ValueError on invalid input."""
    if not isinstance(password, str) or not password:
        raise ValueError("პაროლი სავალდებულოა.")

    if len(password) < 8:
        raise ValueError("პაროლი უნდა იყოს მინიმუმ 8 სიმბოლო.")

    contains_uppercase = False
    contains_lowercase = False
    contains_digits = False
    allowed_characters = set(ascii_lowercase + ascii_uppercase + digits + punctuation)

    for character in password:
        if character not in allowed_characters:
            raise ValueError("პაროლი შეიძლება შეიცავდეს მხოლოდ ინგლისურ ასოებს, ციფრებს და სიმბოლოებს !@#$%^&*")
        if character in ascii_uppercase:
            contains_uppercase = True
        elif character in ascii_lowercase:
            contains_lowercase = True
        elif character in digits:
            contains_digits = True

    if not contains_uppercase:
        raise ValueError("პაროლი უნდა შეიცავდეს მინიმუმ ერთ დიდ ასოს.")
    if not contains_lowercase:
        raise ValueError("პაროლი უნდა შეიცავდეს მინიმუმ ერთ პატარა ასოს.")
    if not contains_digits:
        raise ValueError("პაროლი უნდა შეიცავდეს მინიმუმ ერთ ციფრს.")
