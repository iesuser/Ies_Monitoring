from app.utils.validators import validate_password, normalize_ge_phone, normalize_email
from app.utils.mail import Mail
from app.utils.url_serializer import UrlSerializer

mail = Mail()
url_serializer = UrlSerializer()

def is_authorized_request():
    from app.utils.auth_utils import is_authorized_request as _is_authorized_request
    return _is_authorized_request()
