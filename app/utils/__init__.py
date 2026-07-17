from app.utils.validators import validate_password, normalize_ge_phone, normalize_email


def is_authorized_request():
    from app.utils.auth_utils import is_authorized_request as _is_authorized_request
    return _is_authorized_request()
